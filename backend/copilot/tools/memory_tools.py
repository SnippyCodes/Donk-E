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
    inspection_id: Optional[str] = None,
    correction_type: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    scope_type: Optional[str] = None,
    scope_id: Optional[str] = None,
    field_name: Optional[str] = None,
    corrected_value: Optional[Any] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Record a data correction (raw or AI analysis) and return cascade impact + conflicts.
    Supports direct invocation (inspection_id, payload) and tool/API invocation (scope_type, scope_id, field_name, corrected_value).
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    # Resolve scope_id / inspection_id
    effective_scope_type = scope_type or "inspection"
    target_id = inspection_id or scope_id or "INS-0001-0001"

    if not inspection_id and scope_id:
        if scope_id.startswith("INS-") or effective_scope_type == "inspection":
            target_id = scope_id
            inspection_id = scope_id
        elif scope_id.startswith("WELL-") or effective_scope_type == "well":
            cursor = conn.cursor()
            cursor.execute("SELECT latest_inspection_id FROM well_now WHERE asset_id = ?", (scope_id,))
            row = cursor.fetchone()
            if row and row[0]:
                inspection_id = row[0]
            else:
                cursor.execute("SELECT inspection_id FROM inspections WHERE asset_id = ? ORDER BY inspected_at DESC LIMIT 1", (scope_id,))
                r2 = cursor.fetchone()
                inspection_id = r2[0] if r2 else scope_id
        else:
            inspection_id = scope_id

    effective_correction_type = correction_type or (
        "raw_correction" if (field_name and "temp" in str(field_name).lower()) else "analysis_correction"
    )

    if payload is None:
        payload = {}
        if field_name:
            payload[field_name] = corrected_value
            if "temp" in str(field_name).lower():
                try:
                    payload["corrected_wellhead_temp"] = float(corrected_value)
                except Exception:
                    payload["corrected_wellhead_temp"] = corrected_value
            elif "spill" in str(field_name).lower() or "volume" in str(field_name).lower():
                try:
                    payload["corrected_volume_bbl"] = float(corrected_value)
                except Exception:
                    payload["corrected_volume_bbl"] = corrected_value

    # Record in ledger
    result = record_feedback(
        conn=conn,
        user_id=user_id,
        entry_type=effective_correction_type,
        scope_type=effective_scope_type,
        scope_id=target_id,
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
    param: Optional[str] = None,
    new_value: Optional[Any] = None,
    param_name: Optional[str] = None,
    override_value: Optional[Any] = None,
    original_value: Any = None,
    reason: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Record a rule parameter override (e.g. changing RCA threshold for T350).
    Supports both direct (param, new_value) and registry schema (param_name, override_value).
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    effective_param = param or param_name or ""
    effective_value = new_value if new_value is not None else override_value

    payload = {
        "param": effective_param,
        "new_value": effective_value,
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
    text: Optional[str] = None,
    fact_text: Optional[str] = None,
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

    effective_text = text or fact_text or ""

    payload = {
        "text": effective_text,
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
    well_id: Optional[str] = None,
    asserted_state: Optional[str] = None,
    asset_id: Optional[str] = None,
    claim_type: Optional[str] = None,
    claim_text: Optional[str] = None,
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

    target_well = well_id or asset_id or ""
    effective_state = asserted_state or claim_text or claim_type or ""
    effective_reason = reason or claim_text or f"User claims well is {effective_state}"

    # First check conflicts
    conflict_result = claims_check(conn, target_well, effective_state, user_id)

    # Record the claim in ledger
    payload = {
        "asserted_state": effective_state,
        "text": effective_reason,
    }

    result = record_feedback(
        conn=conn,
        user_id=user_id,
        entry_type="claim",
        scope_type="well",
        scope_id=target_well,
        payload=payload,
        reason=effective_reason,
        rebuild_derived=False,  # Claims don't change data
    )

    result["conflict_check"] = conflict_result

    if close_conn:
        conn.close()

    return result


def tool_save_recall(
    user_id: str,
    query_text: Optional[str] = None,
    response_summary: Optional[str] = None,
    key: Optional[str] = None,
    value_json: Optional[Any] = None,
    referenced_entities: Optional[List[str]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> str:
    """Save a user's interaction to their private recall memory."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    effective_query = query_text or key or "interaction"
    effective_summary = response_summary or (json.dumps(value_json) if isinstance(value_json, dict) else str(value_json or ""))
    entities = referenced_entities or []
    if isinstance(value_json, dict) and "well_id" in value_json:
        entities.append(value_json["well_id"])

    entry_id = save_interaction(conn, user_id, effective_query, effective_summary, entities)

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
