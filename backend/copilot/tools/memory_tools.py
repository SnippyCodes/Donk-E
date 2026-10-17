"""
memory_tools.py — Tool functions for memory operations (ledger, recall, claims).
These are called by the agent loop or directly by tests.
"""
import json
import sqlite3
from typing import Any, Dict, List, Optional

from backend.copilot.db import get_connection
from backend.copilot.resolver import EntityResolver, resolve_window
from backend.copilot.memory.ledger import record_feedback, get_ledger_entries
from backend.copilot.memory.claims import check as claims_check, check_correction_conflicts, check_spill_disagreement
from backend.copilot.memory.recall import save_interaction, recall_wells, recall_entities, has_conversation_history
from backend.copilot.domain.compliance import evaluate_well_compliance


def tool_record_correction(
    user_id: str,
    inspection_id: str,
    correction_type: str,
    payload: Dict[str, Any],
    reason: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Record a data correction (raw or AI analysis) and return cascade impact + conflicts.

    Args:
        user_id: Server-injected user ID
        inspection_id: The inspection being corrected
        correction_type: "raw_correction" or "analysis_correction"
        payload: Dict with corrected_wellhead_temp, corrected_volume_bbl, etc.
        reason: Human-readable reason
        conn: Optional connection
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    # Record in ledger
    result = record_feedback(
        conn=conn,
        user_id=user_id,
        entry_type=correction_type,
        scope_type="inspection",
        scope_id=inspection_id,
        payload=payload,
        reason=reason,
        rebuild_derived=True,
    )

    # Check for conflicts with inspector notes
    conflict_result = check_correction_conflicts(conn, inspection_id, payload)
    result["correction_conflicts"] = conflict_result

    # Get updated well status
    cursor = conn.cursor()
    cursor.execute("SELECT asset_id FROM inspections WHERE inspection_id = ?", (inspection_id,))
    insp_row = cursor.fetchone()
    if insp_row:
        asset_id = insp_row[0]
        cursor.execute("SELECT is_producing, reason_type, reason_summary FROM well_now WHERE asset_id = ?", (asset_id,))
        wn = cursor.fetchone()
        if wn:
            result["updated_well_status"] = {
                "asset_id": asset_id,
                "is_producing": bool(wn[0]),
                "reason_type": wn[1],
                "reason_summary": wn[2],
            }

        # Check if spill became reportable (for analysis corrections)
        if "corrected_volume_bbl" in payload:
            new_vol = payload["corrected_volume_bbl"]
            is_now_reportable = new_vol >= 5.0
            result["spill_status"] = {
                "volume_bbl": new_vol,
                "is_reportable": is_now_reportable,
            }

            if is_now_reportable:
                # Check SR-01 compliance
                start_date, end_date = resolve_window("last 12 months", conn)
                audit = evaluate_well_compliance(asset_id, start_date, end_date, conn)

                sr01_breaches = [b for b in audit["breaches"] if b["protocol_id"] == "SR-01"]
                sr03_breaches = [b for b in audit["breaches"] if b["protocol_id"] == "SR-03"]

                result["compliance_impact"] = {
                    "sr01_breach": len(sr01_breaches) > 0,
                    "sr01_details": sr01_breaches,
                    "sr03_breach": len(sr03_breaches) > 0,
                    "sr03_details": sr03_breaches,
                }

    if close_conn:
        conn.close()

    return result


def tool_record_rule_override(
    user_id: str,
    scope_type: str,
    scope_id: str,
    param: str,
    new_value: Any,
    original_value: Any = None,
    reason: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Record a rule parameter override (e.g. changing RCA threshold for T350).

    Args:
        user_id: Server-injected user ID
        scope_type: "well_type", "well", or "fleet"
        scope_id: e.g. "T350", "WELL-0001", "fleet"
        param: Parameter name from rules.yaml
        new_value: New parameter value
        original_value: Original value for reference
        reason: Human-readable reason
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    payload = {
        "param": param,
        "new_value": new_value,
        "original_value": original_value,
    }

    result = record_feedback(
        conn=conn,
        user_id=user_id,
        entry_type="rule_override",
        scope_type=scope_type,
        scope_id=scope_id,
        payload=payload,
        reason=reason,
        rebuild_derived=True,
    )

    if close_conn:
        conn.close()

    return result


def tool_record_well_fact(
    user_id: str,
    well_id: str,
    text: str,
    note_type: str = "operational",
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Record a fact about a well (e.g. planned shut-in)."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    payload = {
        "text": text,
        "note_type": note_type,
        "well_id": well_id,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }

    result = record_feedback(
        conn=conn,
        user_id=user_id,
        entry_type="well_fact",
        scope_type="well",
        scope_id=well_id,
        payload=payload,
        rebuild_derived=True,
    )

    if close_conn:
        conn.close()

    return result


def tool_record_claim(
    user_id: str,
    well_id: str,
    asserted_state: str,
    reason: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Record a user's claim about a well state and check for conflicts.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    # First check conflicts
    conflict_result = claims_check(conn, well_id, asserted_state, user_id)

    # Record the claim in ledger
    payload = {
        "asserted_state": asserted_state,
        "text": reason or f"User claims well is {asserted_state}",
    }

    result = record_feedback(
        conn=conn,
        user_id=user_id,
        entry_type="claim",
        scope_type="well",
        scope_id=well_id,
        payload=payload,
        reason=reason,
        rebuild_derived=False,  # Claims don't change data
    )

    result["conflict_check"] = conflict_result

    if close_conn:
        conn.close()

    return result


def tool_save_recall(
    user_id: str,
    query_text: str,
    response_summary: str,
    referenced_entities: Optional[List[str]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> str:
    """Save a user's interaction to their private recall memory."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    entry_id = save_interaction(conn, user_id, query_text, response_summary, referenced_entities)

    if close_conn:
        conn.close()

    return entry_id


def tool_recall_wells(
    user_id: str,
    lookback_days: int = 7,
    conn: Optional[sqlite3.Connection] = None,
) -> List[str]:
    """Recall well IDs from a user's private memory."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    wells = recall_wells(conn, user_id, lookback_days)

    if close_conn:
        conn.close()

    return wells


def tool_get_repair_costs_for_wells(
    well_ids: List[str],
    year: str = "2026",
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, float]:
    """
    Get total repair costs for a list of wells in a given year.
    Used to answer Q11 "what have repairs cost this year?"
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    costs = {}
    for well_id in well_ids:
        cursor.execute("""
            SELECT COALESCE(SUM(cost_total), 0) as total_cost
            FROM maintenance
            WHERE asset_id = ?
              AND started_at >= ?
              AND started_at <= ?
        """, (well_id, f"{year}-01-01", f"{year}-12-31T23:59:59Z"))
        row = cursor.fetchone()
        costs[well_id] = round(row[0], 0) if row else 0.0

    if close_conn:
        conn.close()

    return costs


def tool_get_rca_wells(
    area_id: str,
    equipment_kind: str = "pump jack",
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Get wells needing root-cause analysis on a specific equipment kind.
    Uses ParameterResolver which respects ledger-based rule overrides.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    from backend.copilot.domain.params import ParameterResolver
    params = ParameterResolver(conn)
    cursor = conn.cursor()

    # Get all wells in the area
    cursor.execute("SELECT asset_id, well_type FROM assets WHERE area_id = ?", (area_id,))
    wells = cursor.fetchall()

    # For each well, check if it needs RCA
    rca_wells = []
    start_date, end_date = resolve_window("last 12 months", conn)

    for w in wells:
        well_id = w["asset_id"]
        well_type = w["well_type"]

        # Get the RCA threshold for this well (respects overrides)
        rca_thresh_result = params.get_param("rca_corrective_count", well_id=well_id, well_type=well_type, default=3)
        rca_thresh = rca_thresh_result["value"]

        # Check if the param has a more specific key for the equipment
        rca_param_name = f"rca_{equipment_kind.replace(' ', '_')}_repairs"
        rca_equip_result = params.get_param(rca_param_name, well_id=well_id, well_type=well_type)
        if rca_equip_result["value"] is not None:
            rca_thresh = rca_equip_result["value"]

        eq_db = equipment_kind.replace(" ", "_").lower()
        # Count corrective repairs on this equipment
        cursor.execute("""
            SELECT COUNT(*) as cnt, GROUP_CONCAT(maintenance_id, ', ') as mnt_ids
            FROM maintenance
            WHERE asset_id = ?
              AND maintenance_type = 'corrective'
              AND (equipment_kind = ? OR equipment_kind = ?)
              AND started_at >= ?
              AND started_at <= ?
        """, (well_id, equipment_kind, eq_db, start_date, f"{end_date}T23:59:59Z"))
        row = cursor.fetchone()
        cnt = row[0]

        if cnt >= rca_thresh:
            rca_wells.append({
                "well_id": well_id,
                "well_type": well_type,
                "repair_count": cnt,
                "threshold": rca_thresh,
                "threshold_scope": rca_equip_result.get("scope") or rca_thresh_result.get("scope", "default"),
                "maintenance_ids": row[1].split(", ") if row[1] else [],
            })

    rca_wells.sort(key=lambda x: x["well_id"])

    if close_conn:
        conn.close()

    return {
        "area_id": area_id,
        "equipment_kind": equipment_kind,
        "rca_wells": rca_wells,
        "well_ids": [w["well_id"] for w in rca_wells],
    }
