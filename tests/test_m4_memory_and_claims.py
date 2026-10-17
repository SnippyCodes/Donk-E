"""
tests/test_m4_memory_and_claims.py — Verification suite for Milestone M4.

Tests:
  1. Q11 & Q16: Multi-user private session recall + strict user isolation + shared shut-in note.
  2. Q12: INS-0164-0205 temp correction (24 -> 41 °C), status flip, conflict detection.
  3. Q13: INS-0151-0201 volume correction (4.5 -> 5.4 bbl), SR-01/RC-02 compliance breach.
  4. Q14: T350 RCA threshold override (3 -> 2 repairs) with strict well-type isolation.
  5. Q15: Runtime false-positive spill invalidation overlay.
  6. Q17: Unconfirmed operational claim on WELL-0175 flagged against inspection.
  7. Q18: Note-vs-note conflict resolution on INS-0101-0197 with repair corroboration.
  8. Citation Audit: Assert concrete, verifiable IDs across all M4 payloads.
"""
import pytest
import sqlite3
import yaml
from pathlib import Path

from backend.copilot.config import BASE_DIR
from backend.copilot.db import get_connection, init_db
from backend.copilot.ingest.loader import load_dataset
from backend.copilot.tools.analytics import (
    tool_get_well_status,
    tool_get_area_stopped_wells,
    tool_get_well_compliance_audit,
)
from backend.copilot.tools.memory_tools import (
    tool_get_rca_wells,
    tool_get_repair_costs_for_wells,
)
from src.memory.ledger import (
    record_runtime_correction,
    record_rule_override,
    record_shared_asset_note,
    get_runtime_corrections,
    clear_runtime_memory,
)
from src.domain.claims import (
    check_claim,
    check_note_disagreement,
    check_correction_conflicts,
)
from src.memory.recall import (
    record_turn,
    get_recent_wells,
    resolve_referent_wells,
    get_user_history,
    has_conversation_history,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database has baseline data loaded."""
    conn = get_connection()
    init_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM well_now")
    cnt = cursor.fetchone()[0]
    conn.close()
    if cnt < 200:
        load_dataset()


@pytest.fixture(autouse=True)
def clean_memory_between_tests():
    """Ensure pristine baseline before and after each test."""
    conn = get_connection()
    clear_runtime_memory(conn, rebuild_derived=True)
    conn.close()
    yield
    conn = get_connection()
    clear_runtime_memory(conn, rebuild_derived=True)
    conn.close()


@pytest.fixture(scope="session")
def golden_spec():
    yaml_path = BASE_DIR / "tests" / "golden_cases.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


# ── Test 1: Q11 & Q16 Multi-User Private Recall & Shared Knowledge ──

def test_q11_q16_private_recall_and_shared_knowledge():
    """
    Q11 & Q16:
      - Michael Turner (U-201) discusses wells ['WELL-0121', 'WELL-0138', 'WELL-0107'].
      - Later asks: 'For the three wells we discussed yesterday, what have repairs cost this year?'
      - System resolves those exact wells, computes costs.
      - Jessica Reed (U-202) asks the same question: gets [] (strict privacy isolation).
      - Jake Morales (U-102) logs shared shut-in on WELL-0007: visible to Michael Turner.
    """
    conn = get_connection()

    # Step 1: Michael Turner discusses Q6 top 3 wells
    turn_id = record_turn(
        user_id="U-201",
        conn=conn,
        query_text="Top downtime wells in Northeast Block 7?",
        response_summary="WELL-0121, WELL-0138, and WELL-0107 had highest downtime.",
        last_discussed_wells=["WELL-0121", "WELL-0138", "WELL-0107"],
        session_date="2026-10-16",
    )
    assert turn_id.startswith("TURN-")

    # Step 2: Michael Turner resolves referent wells (Q11)
    recalled_m = resolve_referent_wells("U-201", conn, query_text="the three wells we discussed yesterday")
    assert recalled_m == ["WELL-0121", "WELL-0138", "WELL-0107"]

    # Calculate repair costs for 2026
    costs = tool_get_repair_costs_for_wells(recalled_m, year="2026", conn=conn)
    assert costs["WELL-0121"] == 25794.0
    assert costs["WELL-0138"] == 46942.0
    assert costs["WELL-0107"] == 5176.0

    # Step 3: Jessica Reed queries referent wells (Q16 private memory test)
    assert not has_conversation_history("U-202", conn)
    recalled_j = resolve_referent_wells("U-202", conn, query_text="the three wells we discussed yesterday")
    assert recalled_j == []  # Zero cross-account leakage!

    # Step 4: Jake Morales logs shared operational shut-in note on WELL-0007 (Q16 shared knowledge)
    shared_note = record_shared_asset_note(
        conn=conn,
        asset_id="WELL-0007",
        author_user_id="U-102",
        note_text="WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.",
        valid_from="2026-10-17",
        valid_to="2026-10-27",
        reason="Planned workover notification",
    )
    assert shared_note["note_id"].startswith("SAN-")

    # Michael Turner checks planned downtime on WELL-0007
    cursor = conn.cursor()
    cursor.execute("""
        SELECT note_id, note_text, author_user_id
        FROM shared_asset_notes
        WHERE asset_id = 'WELL-0007' AND status = 'confirmed'
    """)
    s_row = cursor.fetchone()
    assert s_row is not None
    assert "shut in from 17 Oct" in s_row["note_text"]
    assert s_row["author_user_id"] == "U-102"

    conn.close()


# ── Test 2: Q12 Temp Correction & Physical Conflict Detection ──

def test_q12_temp_correction_and_conflict(golden_spec):
    """
    Q12:
      - Raw reading on INS-0164-0205 has wellhead_temp_c = 24.0 °C (ambient 18.0 °C, delta 6.0 °C < 15.0 °C -> not producing).
      - Inspector Tyler Hughes noted: "Pump jack not moving."
      - Michael Turner submits correction: wellhead_temp_c = 41.0 °C.
      - System:
        1. Flags conflict against inspector's physical observation ("Pump jack not moving.").
        2. Applies runtime overlay: effective temp becomes 41.0 °C, flipping is_producing to True.
        3. Area NE-08 non-producing count drops from 4 to 3 (removing WELL-0164).
        4. Cites both original_value (24.0) and corrected_value (41.0).
    """
    conn = get_connection()
    spec = golden_spec["Q12"]

    # Pre-check conflict before writing correction
    conflict_check = check_correction_conflicts(
        conn=conn,
        inspection_id=spec["inspection_id"],
        corrected_fields={"corrected_wellhead_temp": spec["corrected_wellhead_temp"]},
    )
    assert conflict_check["has_conflict"] is True
    assert any("Pump jack not moving." in c["detail"] for c in conflict_check["conflicts"])
    assert spec["inspection_id"] in conflict_check["citations"]

    # Record the runtime correction
    corr = record_runtime_correction(
        conn=conn,
        target_type="inspection",
        target_id=spec["inspection_id"],
        asset_id="WELL-0164",
        field_name="wellhead_temp_c",
        original_value=spec["original_wellhead_temp"],
        corrected_value=spec["corrected_wellhead_temp"],
        author_user_id=spec["user_id"],
        reason="Field crew re-measured wellhead with calibrated probe",
        status="confirmed",
    )

    assert corr["correction_id"].startswith("COR-")
    assert corr["cascade_impact"]["producing_status_changed"]["before"] is False
    assert corr["cascade_impact"]["producing_status_changed"]["after"] is True
    assert corr["cascade_impact"]["inspector_note"] == spec["expected"]["conflicting_inspector_note"]

    # Check updated well status
    status = tool_get_well_status("WELL-0164", conn=conn)
    assert status["data"]["is_producing"] == 1
    assert status["data"]["wellhead_temp_c"] == 41.0

    # Re-evaluate Q2 stopped wells in NE-08
    stopped = tool_get_area_stopped_wells("NE-08", conn=conn)
    assert stopped["count"] == spec["expected"]["q2_reeval_count"]
    stopped_ids = [w["well_id"] for w in stopped["wells"]]
    assert spec["expected"]["removed_well"] not in stopped_ids

    conn.close()


# ── Test 3: Q13 Spill Volume Correction & Reportable Compliance Trigger ──

def test_q13_spill_volume_correction_compliance(golden_spec):
    """
    Q13:
      - INS-0151-0201 has AI estimated spill volume 4.5 bbl (< 5.0 bbl -> non-reportable).
      - Michael Turner records corrected volume 5.4 bbl (>= 5.0 bbl -> reportable).
      - Effective overlay triggers:
        1. is_reportable becomes True in spills table.
        2. SR-01 breach triggered (written report due in 24 hours, not filed).
        3. SR-03 agency verification deadline due 60 days from spill (2026-11-23).
    """
    conn = get_connection()
    spec = golden_spec["Q13"]

    corr = record_runtime_correction(
        conn=conn,
        target_type="inspection",
        target_id=spec["inspection_id"],
        asset_id="WELL-0151",
        field_name="spill_volume_bbl",
        original_value=spec["original_volume_bbl"],
        corrected_value=spec["corrected_volume_bbl"],
        author_user_id=spec["user_id"],
        reason="Field crew tape measurement confirmed 5.4 bbl",
        status="confirmed",
    )

    assert corr["correction_id"].startswith("COR-")
    assert corr["cascade_impact"]["reportable_status_changed"]["before"] is False
    assert corr["cascade_impact"]["reportable_status_changed"]["after"] is True

    # Audit compliance for WELL-0151
    audit = tool_get_well_compliance_audit("WELL-0151", window_expr="last 12 months", conn=conn)
    breach_protocols = [b["protocol_id"] for b in audit["breaches"]]
    assert "SR-01" in breach_protocols

    # Verify SR-03 due date in compliance impact
    sr03_details = corr["cascade_impact"]["compliance_impact"].get("sr03_details", [])
    assert len(sr03_details) > 0
    assert any(spec["expected"]["sr03_due_date"] in d.get("due_date", "") or spec["expected"]["sr03_due_date"] in d.get("description", "") for d in sr03_details)

    conn.close()


# ── Test 4: Q14 Well-Type Policy Override & Scope Isolation ──

def test_q14_well_type_rule_override_isolation(golden_spec):
    """
    Q14:
      - Michael Turner lowers T350 pump jack RCA threshold from 3 to 2 corrective repairs.
      - WELL-0120 (T350, 2 repairs) now needs RCA.
      - WELL-0102 (T200, 2 repairs) MUST NOT be affected (T200 threshold remains 3).
      - Strict well-type scope isolation guaranteed.
    """
    conn = get_connection()
    spec = golden_spec["Q14"]

    # Pre-override check: WELL-0120 not in RCA list
    pre = tool_get_rca_wells("NE-07", equipment_kind="pump jack", conn=conn)
    assert spec["expected"]["added_well"] not in pre["well_ids"]

    # Record rule override
    ovr = record_rule_override(
        conn=conn,
        well_type=spec["well_type"],
        rule_field=spec["param"],
        equipment_kind="pump_jack",
        original_value=spec["original_value"],
        new_value=spec["new_value"],
        author_user_id=spec["user_id"],
        reason="Team lowered T350 pump jack RCA threshold to 2",
    )
    assert ovr["override_id"].startswith("OVR-")

    # Post-override check:
    post = tool_get_rca_wells("NE-07", equipment_kind="pump jack", conn=conn)
    post_ids = post["well_ids"]

    # WELL-0120 (T350) added
    assert spec["expected"]["added_well"] in post_ids
    # WELL-0102 (T200) strictly NOT added
    assert spec["expected"]["not_added_t200_well"] not in post_ids
    # Exact full set
    assert sorted(post_ids) == sorted(spec["expected"]["wells_needing_rca"])

    conn.close()


# ── Test 5: Q15 Runtime False-Positive Spill Invalidation Overlay ──

def test_q15_runtime_false_positive_spill_invalidation():
    """
    Q15:
      - Operator invalidates a false-positive spill at runtime (e.g. rainwater puddle).
      - Corrected field: spill_detected = 0.
      - Result: eff_inspection marks is_spill_corrected = 1 and effective_spill_detected = 0.
      - Spill is excluded from the active spills table.
    """
    conn = get_connection()

    # Pick an inspection that has a detected spill
    cursor = conn.cursor()
    cursor.execute("SELECT inspection_id, asset_id, spill_est_volume_bbl FROM inspections WHERE spill_detected = 1 LIMIT 1")
    row = cursor.fetchone()
    insp_id = row[0]
    asset_id = row[1]
    orig_vol = row[2]

    # Invalidate spill at runtime
    corr = record_runtime_correction(
        conn=conn,
        target_type="inspection",
        target_id=insp_id,
        asset_id=asset_id,
        field_name="spill_detected",
        original_value=1,
        corrected_value=0,
        author_user_id="U-401",
        reason="Inspection confirmed rainwater puddle mixed with clay, zero crude oil present",
        status="confirmed",
    )
    assert corr["correction_id"].startswith("COR-")

    # Check effective inspection
    cursor.execute("""
        SELECT is_spill_corrected, effective_spill_detected, correction_note_id
        FROM eff_inspection WHERE inspection_id = ?
    """, (insp_id,))
    eff = cursor.fetchone()
    assert eff[0] == 1  # is_spill_corrected
    assert eff[1] == 0  # effective_spill_detected
    assert eff[2] == corr["correction_id"]

    # Check that it is removed from active spills table
    cursor.execute("SELECT COUNT(*) FROM spills WHERE inspection_id = ?", (insp_id,))
    assert cursor.fetchone()[0] == 0

    conn.close()


# ── Test 6: Q17 Unconfirmed Operational Claim Conflict ──

def test_q17_unconfirmed_operational_claim_conflict():
    """
    Q17:
      1. Michael Turner (U-201) records fact that WELL-0175 is shut in for planned work.
      2. Tyler Hughes (U-204) claims 'WELL-0175 is running fine'.
      3. System cross-checks:
         - Latest inspection (INS-0175-0204) shows wellhead delta 0.4 °C (not producing).
         - Michael Turner's shared note states well is shut in.
         - Returns warning, flags status='unconfirmed', requires user confirmation,
           cites INS-0175-0204 and Michael Turner's note.
    """
    conn = get_connection()

    # 1. Michael Turner records shut-in fact
    record_shared_asset_note(
        conn=conn,
        asset_id="WELL-0175",
        author_user_id="U-201",
        note_text="WELL-0175 has been shut in for planned work since 14 Oct.",
    )

    # 2. Tyler Hughes claims well is running fine
    check = check_claim(
        conn=conn,
        well_id="WELL-0175",
        asserted_state="running_fine",
        user_id="U-204",
    )

    assert check["verdict"] in ("contradicts_data", "contradicts_other_note")
    assert check["severity"] == "warning"
    assert check["requires_confirmation"] is True
    assert not check["is_producing_per_data"]

    conflict_types = [c["type"] for c in check["conflicts"]]
    assert "contradicts_data" in conflict_types
    assert "contradicts_other_note" in conflict_types

    # Must cite inspection and shared note
    assert any("INS-0175" in cit for cit in check["citations"])
    assert any("SAN-" in cit or "CTX-" in cit or "LEDGER-" in cit for cit in check["citations"])

    conn.close()


# ── Test 7: Q18 Note-vs-Note Disagreement Resolution ──

def test_q18_note_vs_note_conflict_resolution():
    """
    Q18:
      - 'Was the 20 Aug spill at WELL-0101 real oil?'
      - AI detected 1.0 bbl spill at INS-0101-0197 ('Oil sheen around cellar.').
      - CTX-0101-002: Ryan Brooks thought produced water.
      - CTX-0101-003: Chris Dalton (HSE) sampled stain and confirmed crude oil.
      - Repair MNT-0101-029 corroborates spill repair.
      - Resolution: Detection stands as real oil; dispute explicitly surfaced with both citations.
    """
    conn = get_connection()

    res = check_note_disagreement(conn, "INS-0101-0197")
    assert res["has_disagreement"] is True
    assert res["effective_is_real"] is True
    assert res["repair_done"] is True
    assert res["repair_id"] == "MNT-0101-029"

    # Verify all four evidence citations are present
    assert "INS-0101-0197" in res["citations"]
    assert "CTX-0101-002" in res["citations"]
    assert "CTX-0101-003" in res["citations"]
    assert "MNT-0101-029" in res["citations"]

    authors = [n["author_name"] for n in res["disagree_notes"]]
    assert "Ryan Brooks" in authors
    assert "Chris Dalton" in authors

    conn.close()


# ── Test 8: Citation Audit Test ──

def test_citation_audit():
    """
    Assert that every M4 return payload contains non-empty, concrete source citations
    (INS-*, CTX-*, MNT-*, COR-*, OVR-*, SAN-*, or manual file IDs).
    """
    conn = get_connection()

    # 1. Runtime correction citation audit
    corr = record_runtime_correction(
        conn=conn,
        target_type="inspection",
        target_id="INS-0164-0205",
        asset_id="WELL-0164",
        field_name="wellhead_temp_c",
        original_value=24.0,
        corrected_value=41.0,
        author_user_id="U-201",
        reason="Audit test",
        status="confirmed",
    )
    assert len(corr["citations"]) >= 2
    assert any(c.startswith("COR-") for c in corr["citations"])
    assert any(c.startswith("INS-") for c in corr["citations"])

    # 2. Rule override citation audit
    ovr = record_rule_override(
        conn=conn,
        well_type="T350",
        rule_field="rca_pump_jack_repairs",
        new_value=2,
        author_user_id="U-201",
    )
    assert len(ovr["citations"]) >= 1
    assert any(c.startswith("OVR-") for c in ovr["citations"])

    # 3. Shared note citation audit
    snote = record_shared_asset_note(
        conn=conn,
        asset_id="WELL-0007",
        author_user_id="U-102",
        note_text="Audit test shut-in",
    )
    assert len(snote["citations"]) >= 1
    assert any(c.startswith("SAN-") for c in snote["citations"])

    # 4. Claims check citation audit
    claim_audit = check_claim(conn, "WELL-0175", "running_fine", "U-204")
    assert len(claim_audit["citations"]) >= 1
    assert any(c.startswith("INS-") for c in claim_audit["citations"])

    # 5. Note disagreement citation audit
    diag_audit = check_note_disagreement(conn, "INS-0101-0197")
    assert len(diag_audit["citations"]) >= 3
    assert any(c.startswith("INS-") for c in diag_audit["citations"])
    assert any(c.startswith("CTX-") for c in diag_audit["citations"])

    conn.close()
