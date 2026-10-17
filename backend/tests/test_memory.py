"""
test_memory.py — Tests for Q11–Q14 (memory, feedback, ledger, recall, claims).
"""
import json
import pytest
import yaml
from pathlib import Path

from backend.copilot.config import BASE_DIR
from backend.copilot.db import get_connection, init_db
from backend.copilot.ingest.loader import load_dataset
from backend.copilot.tools.memory_tools import (
    tool_record_correction,
    tool_record_rule_override,
    tool_record_claim,
    tool_save_recall,
    tool_recall_wells,
    tool_get_repair_costs_for_wells,
    tool_get_rca_wells,
)
from backend.copilot.tools.analytics import (
    tool_get_area_stopped_wells,
    tool_get_well_status,
)
from backend.copilot.memory.recall import has_conversation_history


from backend.copilot.memory.ledger import clear_ledger


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


@pytest.fixture(autouse=True)
def clean_ledger_between_tests():
    """Ensure each test in test_memory starts and ends with clean ledger."""
    conn = get_connection()
    clear_ledger(conn, rebuild_derived=True)
    conn.close()
    yield
    conn = get_connection()
    clear_ledger(conn, rebuild_derived=True)
    conn.close()


@pytest.fixture(scope="session")
def golden_spec():
    """Load golden test specifications from tests/golden_cases.yaml."""
    yaml_path = BASE_DIR / "tests" / "golden_cases.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


def test_q11_recall_past_conversation(golden_spec):
    """
    Q11: Remembering past conversations.
    Day 1: Michael Turner asks Q6 (top downtime in NE-07 → WELL-0121, WELL-0138, WELL-0107).
    Day 2: Michael Turner asks "For the three wells we discussed yesterday, what have repairs cost this year?"
    Expected: recalled wells WELL-0121, WELL-0138, WELL-0107 with costs.
    """
    spec = golden_spec["Q11"]
    conn = get_connection()

    # Simulate Day 1: Save Q6 interaction for Michael Turner
    tool_save_recall(
        user_id=spec["user_id"],
        query_text="Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months?",
        response_summary="Top 3 wells by downtime: WELL-0121 (49 days), WELL-0138 (42 days), WELL-0107 (42 days)",
        referenced_entities=["WELL-0121", "WELL-0138", "WELL-0107"],
        conn=conn,
    )

    # Day 2: Recall the wells
    recalled_wells = tool_recall_wells(user_id=spec["user_id"], conn=conn)
    assert set(spec["expected"]["recalled_wells"]).issubset(set(recalled_wells)), \
        f"Expected {spec['expected']['recalled_wells']} in {recalled_wells}"

    # Get repair costs
    costs = tool_get_repair_costs_for_wells(recalled_wells[:3], year="2026", conn=conn)

    assert costs["WELL-0121"] == spec["expected"]["costs"]["WELL-0121"]
    assert costs["WELL-0138"] == spec["expected"]["costs"]["WELL-0138"]
    assert costs["WELL-0107"] == spec["expected"]["costs"]["WELL-0107"]

    conn.close()


def test_q12_raw_data_correction(golden_spec):
    """
    Q12: Correcting wrong raw data.
    Michael Turner corrects INS-0164-0205 wellhead temp from 24.0 to 41.0 °C.
    Expected:
      - WELL-0164 is now producing oil (delta 21.1 °C ≥ 15.0 threshold for T200)
      - Conflict detected: inspector noted "Pump jack not moving."
      - Q2 reeval: 3 wells not producing (WELL-0164 removed)
    """
    spec = golden_spec["Q12"]
    conn = get_connection()

    # Apply the correction
    result = tool_record_correction(
        user_id=spec["user_id"],
        inspection_id=spec["inspection_id"],
        correction_type="raw_correction",
        payload={
            "corrected_wellhead_temp": spec["corrected_wellhead_temp"],
            "original_wellhead_temp": spec["original_wellhead_temp"],
            "reason": "Handheld thermal gun was faulty; field crew re-measured",
        },
        conn=conn,
    )

    assert result["entry_id"].startswith("LEDGER-")

    # Verify well is now producing
    well_status = result.get("updated_well_status", {})
    assert well_status.get("is_producing") == spec["expected"]["updated_is_producing"], \
        f"Expected producing={spec['expected']['updated_is_producing']}, got {well_status}"

    # Verify conflict detected with inspector note
    conflicts = result.get("correction_conflicts", {})
    assert conflicts.get("has_conflict") == spec["expected"]["conflict_detected"], \
        f"Expected conflict={spec['expected']['conflict_detected']}, got {conflicts}"

    # Check that the conflicting note mentions "Pump jack not moving."
    if spec["expected"]["conflict_detected"]:
        conflict_details = conflicts.get("conflicts", [])
        found_pump_jack = False
        for c in conflict_details:
            if "Pump jack not moving" in c.get("detail", ""):
                found_pump_jack = True
                break
        # Also check inspector_note field
        if not found_pump_jack and conflicts.get("inspector_note"):
            found_pump_jack = "Pump jack not moving" in conflicts["inspector_note"]
        assert found_pump_jack, f"Expected 'Pump jack not moving.' in conflict details: {conflict_details}"

    # Re-evaluate Q2: NE-08 non-producing wells
    q2_result = tool_get_area_stopped_wells("Northeast Block 8", conn=conn)
    assert q2_result["count"] == spec["expected"]["q2_reeval_count"], \
        f"Expected {spec['expected']['q2_reeval_count']} non-producing wells, got {q2_result['count']}"

    # WELL-0164 should no longer be in the list
    q2_well_ids = [w["well_id"] for w in q2_result["wells"]]
    assert spec["expected"]["removed_well"] not in q2_well_ids, \
        f"Expected {spec['expected']['removed_well']} removed from stopped wells, found in {q2_well_ids}"

    conn.close()


def test_q13_analysis_correction(golden_spec):
    """
    Q13: Correcting the AI's analysis.
    Michael Turner corrects WELL-0151 spill from 4.5 to 5.4 bbl.
    Expected:
      - Spill becomes reportable (≥5 bbl)
      - SR-01 breach: no written notice filed within 24 hours
      - SR-03 due date: 2026-11-23 (60 days from 2026-09-24)
    """
    spec = golden_spec["Q13"]
    conn = get_connection()

    result = tool_record_correction(
        user_id=spec["user_id"],
        inspection_id=spec["inspection_id"],
        correction_type="analysis_correction",
        payload={
            "corrected_volume_bbl": spec["corrected_volume_bbl"],
            "original_volume_bbl": spec["original_volume_bbl"],
        },
        reason="Field crew measured actual volume",
        conn=conn,
    )

    assert result["entry_id"].startswith("LEDGER-")

    # Verify spill is now reportable
    spill_status = result.get("spill_status", {})
    assert spill_status.get("is_reportable") == spec["expected"]["becomes_reportable"], \
        f"Expected reportable={spec['expected']['becomes_reportable']}, got {spill_status}"

    # Check SR-01 breach
    compliance = result.get("compliance_impact", {})
    assert compliance.get("sr01_breach") == spec["expected"]["sr01_breach"], \
        f"Expected SR-01 breach={spec['expected']['sr01_breach']}, got {compliance}"

    # Check SR-03 due date
    sr03_details = compliance.get("sr03_details", [])
    if spec["expected"].get("sr03_due_date") and sr03_details:
        found_date = False
        for d in sr03_details:
            if spec["expected"]["sr03_due_date"] in d.get("due_date", ""):
                found_date = True
                break
            if spec["expected"]["sr03_due_date"] in d.get("description", ""):
                found_date = True
                break
        assert found_date, f"Expected SR-03 due date {spec['expected']['sr03_due_date']} in {sr03_details}"

    conn.close()


def test_q14_type_rule_override(golden_spec):
    """
    Q14: A rule for a whole well type.
    Michael Turner: "Note for all T350 wells: pump jack RCA after 2 repairs, not 3."
    Expected:
      - WELL-0120 (T350) added to RCA list (has 2 repairs → now meets threshold)
      - WELL-0102 (T200) NOT added (T200 threshold unchanged at 3)
      - Full RCA list: WELL-0108, WELL-0120, WELL-0121, WELL-0138
    """
    spec = golden_spec["Q14"]
    conn = get_connection()

    # First, check pre-override state: which wells in NE-07 need RCA on pump jack?
    pre_override = tool_get_rca_wells("NE-07", equipment_kind="pump jack", conn=conn)
    pre_well_ids = pre_override["well_ids"]
    # WELL-0120 should NOT be in pre-override list (only has 2 repairs, threshold is 3)
    assert spec["expected"]["added_well"] not in pre_well_ids, \
        f"Expected {spec['expected']['added_well']} NOT in pre-override list, found in {pre_well_ids}"

    # Apply the rule override for T350
    result = tool_record_rule_override(
        user_id=spec["user_id"],
        scope_type="well_type",
        scope_id="T350",
        param=spec["param"],
        new_value=spec["new_value"],
        original_value=spec["original_value"],
        reason="Team wants pump jack RCA after 2 repairs for T350 wells",
        conn=conn,
    )

    assert result["entry_id"].startswith("LEDGER-")

    # Re-check: which wells in NE-07 need RCA?
    post_override = tool_get_rca_wells("NE-07", equipment_kind="pump jack", conn=conn)
    post_well_ids = post_override["well_ids"]

    # WELL-0120 (T350) should now be included
    assert spec["expected"]["added_well"] in post_well_ids, \
        f"Expected {spec['expected']['added_well']} in post-override list, found {post_well_ids}"

    # WELL-0102 (T200) should NOT be included
    assert spec["expected"]["not_added_t200_well"] not in post_well_ids, \
        f"Expected {spec['expected']['not_added_t200_well']} NOT in post-override list, found {post_well_ids}"

    # Full expected list
    assert sorted(post_well_ids) == sorted(spec["expected"]["wells_needing_rca"]), \
        f"Expected {sorted(spec['expected']['wells_needing_rca'])}, got {sorted(post_well_ids)}"

    conn.close()


def test_q15_correction_reaches_other_users(golden_spec):
    """
    Q15: A correction reaches other users (follows Q12 and Q13).
    Part 1: Michael Turner corrected INS-0164-0205 to 41.0 °C.
            Jessica Reed (U-202) asks: "Is WELL-0164 producing oil right now?"
            Expected: producing=True, mentions conflict with inspector's "Pump jack not moving."
    Part 2: Michael Turner corrected INS-0151-0201 to 5.4 bbl.
            Laura Simmons (U-401) asks: Which spills in NE-08 in last 90 days needed report?
            Expected: WELL-0151 is reportable (5.4 bbl >= 5.0) with SR-01 breach.
    """
    conn = get_connection()

    # Apply Q12 correction
    q12_spec = golden_spec["Q12"]
    tool_record_correction(
        user_id=q12_spec["user_id"],
        inspection_id=q12_spec["inspection_id"],
        correction_type="raw_correction",
        payload={"corrected_wellhead_temp": q12_spec["corrected_wellhead_temp"],
                 "original_wellhead_temp": q12_spec["original_wellhead_temp"]},
        reason="Field crew re-measured wellhead",
        conn=conn,
    )

    # Apply Q13 correction
    q13_spec = golden_spec["Q13"]
    tool_record_correction(
        user_id=q13_spec["user_id"],
        inspection_id=q13_spec["inspection_id"],
        correction_type="analysis_correction",
        payload={"corrected_volume_bbl": q13_spec["corrected_volume_bbl"],
                 "original_volume_bbl": q13_spec["original_volume_bbl"]},
        reason="Field crew measured 5.4 bbl",
        conn=conn,
    )

    # Jessica Reed checks WELL-0164 status
    status = tool_get_well_status("WELL-0164", conn=conn)
    assert status["data"]["is_producing"] == 1
    assert status["data"]["wellhead_temp_c"] == 41.0
    assert status["data"]["inspector_note"] == "Pump jack not moving."

    # Laura Simmons queries reportable spills in NE-08
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.asset_id, s.inspection_id, s.volume_bbl, s.is_reportable
        FROM spills s
        WHERE s.area_id = 'NE-08'
          AND s.is_reportable = 1
          AND s.date >= '2026-07-19'
    """)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["asset_id"] == "WELL-0151"
    assert rows[0]["volume_bbl"] == 5.4

    conn.close()


def test_q16_shared_knowledge_private_memory():
    """
    Q16: Shared knowledge, private memory.
    1. Jake Morales (U-102): "FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover."
    2. Michael Turner (U-201): "Is any downtime planned for WELL-0007?" -> Sees Jake's note.
    3. Jessica Reed (U-202): "For the three wells we discussed yesterday, what have repairs cost this year?"
       -> Copilot says no earlier conversation with Jessica Reed (private memory enforced).
    """
    conn = get_connection()

    # Step 1: Jake Morales shares operational fact
    from backend.copilot.memory.ledger import record_feedback
    record_feedback(
        conn=conn,
        user_id="U-102",
        entry_type="well_fact",
        scope_type="well",
        scope_id="WELL-0007",
        payload={
            "text": "WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.",
            "note_type": "operational",
            "valid_from": "2026-10-17",
            "valid_to": "2026-10-27",
        },
        reason="Planned workover notification",
        rebuild_derived=False,
    )

    # Step 2: Query planned downtime for WELL-0007
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.entry_id, l.user_id, l.payload_json, u.name as user_name
        FROM ledger l
        LEFT JOIN users u ON l.user_id = u.user_id
        WHERE l.scope_id = 'WELL-0007' AND l.entry_type = 'well_fact'
    """)
    row = cursor.fetchone()
    assert row is not None
    payload = json.loads(row["payload_json"])
    assert "shut in from 17 Oct" in payload["text"]
    assert row["user_name"] == "Jake Morales"

    # Step 3: Jessica Reed checks recall (should have NONE)
    assert not has_conversation_history(conn, "U-202")
    recalled = tool_recall_wells("U-202", conn=conn)
    assert len(recalled) == 0

    conn.close()


def test_q17_people_disagree_with_data():
    """
    Q17: People disagree with the data and with each other.
    1. Michael Turner: "WELL-0175 has been shut in for planned work since 14 Oct."
    2. Tyler Hughes (U-204): "WELL-0175 is running fine."
       -> Contradicts 15 Oct inspection (not producing, delta 0.4 °C) AND Michael Turner's note.
    3. Jake Morales (U-102): "WELL-0001 is back online since 14 Oct."
       -> Contradicts 15 Oct inspection (not producing, delta 3.2 °C, pump jack not moving)
          AND note CTX-0001-003 (return around 20 Oct).
    """
    conn = get_connection()
    from backend.copilot.memory.ledger import record_feedback

    # 1. Michael Turner records fact about WELL-0175
    record_feedback(
        conn=conn,
        user_id="U-201",
        entry_type="well_fact",
        scope_type="well",
        scope_id="WELL-0175",
        payload={"text": "WELL-0175 has been shut in for planned work since 14 Oct.", "note_type": "operational"},
        reason="Shut-in notice",
        rebuild_derived=False,
    )

    # 2. Tyler Hughes claims WELL-0175 is running fine
    claim_res = tool_record_claim(
        user_id="U-204",
        well_id="WELL-0175",
        asserted_state="running_fine",
        conn=conn,
    )
    chk = claim_res["conflict_check"]
    assert chk["verdict"] in ("contradicts_other_note", "contradicts_data")
    assert not chk["is_producing_per_data"]
    # Should cite both inspection and Michael Turner's note
    types = [c["type"] for c in chk["conflicts"]]
    assert "contradicts_data" in types
    assert "contradicts_other_note" in types

    # 3. Jake Morales claims WELL-0001 is back online
    claim_res2 = tool_record_claim(
        user_id="U-102",
        well_id="WELL-0001",
        asserted_state="back_online",
        conn=conn,
    )
    chk2 = claim_res2["conflict_check"]
    assert chk2["verdict"] in ("contradicts_data", "contradicts_other_note")
    assert not chk2["is_producing_per_data"]
    assert "Pump jack not moving." in chk2["inspector_note"]
    # Check that CTX-0001-003 or inspection is in citations
    assert any("INS-0001" in cit for cit in chk2["citations"])

    conn.close()


def test_q18_disagree_on_ai_analysis():
    """
    Q18: People disagree about the AI's analysis.
    "Was the 20 Aug spill at WELL-0101 real oil?"
    - AI flagged 1.0 bbl spill at INS-0101-0197.
    - Ryan Brooks (CTX-0101-002) thought produced water.
    - Chris Dalton (CTX-0101-003) confirmed crude.
    - Repair MNT-0101-029 was done.
    - Detection stands: answer yes with disagreement surfaced.
    """
    conn = get_connection()
    from backend.copilot.memory.claims import check_spill_disagreement

    disagreement = check_spill_disagreement(conn, "INS-0101-0197")
    assert disagreement["has_disagreement"] is True
    assert disagreement["effective_is_real"] is True
    assert disagreement["repair_done"] is True
    assert disagreement["repair_id"] == "MNT-0101-029"
    assert "INS-0101-0197" in disagreement["citations"]
    assert "CTX-0101-002" in disagreement["citations"]
    assert "CTX-0101-003" in disagreement["citations"]
    assert "MNT-0101-029" in disagreement["citations"]

    authors = [n["author_name"] for n in disagreement["disagree_notes"]]
    assert "Ryan Brooks" in authors
    assert "Chris Dalton" in authors

    conn.close()

