"""
test_scope.py — Tests for scope discipline.
Ensures:
  1. T350 rule overrides don't affect T200 wells
  2. Private recall enforces WHERE user_id = ?
  3. Ledger scope_type/scope_id integrity
"""
import pytest
from backend.copilot.db import get_connection
from backend.copilot.ingest.loader import load_dataset
from backend.copilot.memory.recall import save_interaction, recall_wells, has_conversation_history
from backend.copilot.memory.ledger import record_feedback
from backend.copilot.domain.params import ParameterResolver


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure test database is fully loaded before running tests."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM well_now")
    cnt = c.fetchone()[0]
    conn.close()
    if cnt < 200:
        load_dataset()


def test_private_recall_isolation():
    """
    User A's recall must not leak to User B.
    Corresponds to Q16: Jessica Reed cannot see Michael Turner's conversation history.
    """
    conn = get_connection()

    # User A saves interactions
    save_interaction(conn, "U-201", "Q about WELL-0121", "Answer about WELL-0121", ["WELL-0121"])
    save_interaction(conn, "U-201", "Q about WELL-0138", "Answer about WELL-0138", ["WELL-0138"])

    # User B has no history
    user_b_wells = recall_wells(conn, "U-301", lookback_days=30)
    assert len(user_b_wells) == 0, f"User B should have no recall, got {user_b_wells}"

    # User A can recall
    user_a_wells = recall_wells(conn, "U-201", lookback_days=30)
    assert "WELL-0121" in user_a_wells
    assert "WELL-0138" in user_a_wells

    # User B has no conversation history
    assert not has_conversation_history(conn, "U-301", lookback_days=30)
    # User A does
    assert has_conversation_history(conn, "U-201", lookback_days=30)

    conn.close()


def test_rule_override_scope_isolation():
    """
    A T350 rule override must NOT affect T200 wells.
    This is Rule #4 from AGENTS.md: strict scope discipline.
    """
    conn = get_connection()
    params = ParameterResolver(conn)

    # Record a T350 override
    record_feedback(
        conn=conn,
        user_id="U-201",
        entry_type="rule_override",
        scope_type="well_type",
        scope_id="T350",
        payload={"param": "test_scope_param", "new_value": 99},
        rebuild_derived=False,
    )
    # Also insert the param_override entry directly
    import json, uuid, datetime
    entry_id = f"LEDGER-SCOPE-{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
        VALUES (?, ?, ?, 'well_type', 'T350', 'param_override', ?, 'test')
    """, (entry_id, datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"), "U-201",
          json.dumps({"test_scope_param": 99})))
    conn.commit()

    # T350 well should get the override
    result_350 = params.get_param("test_scope_param", well_type="T350")
    assert result_350["value"] == 99, f"T350 should have overridden value 99, got {result_350}"

    # T200 well should NOT get the override
    result_200 = params.get_param("test_scope_param", well_type="T200")
    assert result_200["value"] is None or result_200["scope"] != "well_type" or result_200["scope_id"] != "T350", \
        f"T200 should NOT inherit T350 override, got {result_200}"

    conn.close()


def test_ledger_entry_has_correct_scope():
    """Verify ledger entries have correct scope_type and scope_id."""
    conn = get_connection()

    # Record a well-scoped fact
    result = record_feedback(
        conn=conn,
        user_id="U-201",
        entry_type="well_fact",
        scope_type="well",
        scope_id="WELL-0007",
        payload={"text": "Planned workover from 17 Oct", "note_type": "operational"},
        rebuild_derived=False,
    )

    assert result["scope_type"] == "well"
    assert result["scope_id"] == "WELL-0007"

    # Verify in DB
    cursor = conn.cursor()
    cursor.execute("SELECT scope_type, scope_id FROM ledger WHERE entry_id = ?", (result["entry_id"],))
    row = cursor.fetchone()
    assert row[0] == "well"
    assert row[1] == "WELL-0007"

    conn.close()
