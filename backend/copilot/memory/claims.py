"""
claims.py — Conflict detection for user assertions vs. inspection data and other notes.

Implements claims.check(well_id, asserted_state, as_of) returning:
  - "consistent": assertion agrees with all data
  - "contradicts_data": assertion disagrees with inspection evidence
  - "contradicts_other_note": assertion disagrees with another user's note/claim

Each verdict includes exact citations (INS-..., CTX-..., MNT-...).
"""
import json
import sqlite3
from typing import Any, Dict, List, Optional

from backend.copilot.config import AS_OF
from backend.copilot.db import get_connection


def check(
    conn: sqlite3.Connection,
    well_id: str,
    asserted_state: str,
    user_id: str,
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check whether a user's claim about a well agrees with data and other notes.

    Args:
        conn: Active SQLite connection
        well_id: The asset_id being claimed about
        asserted_state: One of "producing", "not_producing", "shut_in", "running_fine",
                        "back_online", "spill_is_real", "spill_is_not_real"
        user_id: Who is making the claim
        as_of: Reference date (defaults to config.AS_OF)

    Returns:
        Dict with:
          - verdict: "consistent" | "contradicts_data" | "contradicts_other_note"
          - citations: list of evidence IDs
          - conflicts: list of conflict detail dicts
          - inspector_notes: any relevant inspector notes that conflict
    """
    ref_date = as_of or AS_OF
    cursor = conn.cursor()

    # Get latest inspection data from well_now
    cursor.execute("""
        SELECT w.*, u.name as inspector_name_full
        FROM well_now w
        LEFT JOIN users u ON w.inspector_user_id = u.user_id
        WHERE w.asset_id = ?
    """, (well_id,))
    well = cursor.fetchone()

    if not well:
        return {
            "verdict": "unknown",
            "reason": f"Well {well_id} not found in current data.",
            "citations": [],
            "conflicts": [],
        }

    well_data = dict(well)
    is_producing = bool(well_data["is_producing"])
    inspector_note = well_data.get("inspector_note")
    latest_insp_id = well_data["latest_inspection_id"]
    latest_date = well_data["latest_inspected_date"]

    citations: List[str] = [latest_insp_id]
    conflicts: List[Dict[str, Any]] = []

    # Normalize assertion
    norm_state = asserted_state.lower().strip()

    # ── Check against inspection data ──

    if norm_state in ("producing", "running_fine", "back_online"):
        if not is_producing:
            # Assertion says producing, data says not
            conflict = {
                "type": "contradicts_data",
                "detail": (
                    f"The {latest_date} inspection ({latest_insp_id}) shows wellhead "
                    f"only {well_data['delta_temp_c']} °C above air "
                    f"(threshold: {well_data['threshold_temp_delta']} °C). "
                    f"The well is not producing oil."
                ),
                "evidence_id": latest_insp_id,
            }
            conflicts.append(conflict)

            # Check for inspector notes that agree with the data (not producing)
            if inspector_note:
                conflicts.append({
                    "type": "inspector_note_agrees_with_data",
                    "detail": f"Inspector noted: \"{inspector_note}\"",
                    "evidence_id": latest_insp_id,
                })

    elif norm_state in ("not_producing", "shut_in", "down"):
        if is_producing:
            conflict = {
                "type": "contradicts_data",
                "detail": (
                    f"The {latest_date} inspection ({latest_insp_id}) shows wellhead "
                    f"{well_data['delta_temp_c']} °C above air "
                    f"(threshold: {well_data['threshold_temp_delta']} °C). "
                    f"The well IS producing oil."
                ),
                "evidence_id": latest_insp_id,
            }
            conflicts.append(conflict)

    # ── Check against other users' notes/claims ──

    # Get active context notes from other users
    cursor.execute("""
        SELECT cn.note_id, cn.text, cn.author_user_id, u.name as author_name, cn.note_type
        FROM context_notes cn
        LEFT JOIN users u ON cn.author_user_id = u.user_id
        WHERE cn.asset_id = ?
          AND cn.author_user_id != ?
          AND cn.note_type IN ('operational', 'claim', 'correction', 'operator_feedback', 'operator_note')
          AND (cn.valid_to IS NULL OR cn.valid_to >= ?)
        ORDER BY cn.created_at DESC
    """, (well_id, user_id, ref_date))

    other_notes = cursor.fetchall()

    for note in other_notes:
        note_text = note["text"].lower()
        note_id = note["note_id"]
        author_name = note["author_name"] or note["author_user_id"]
        citations.append(note_id)

        # Check for conflicting claims
        if norm_state in ("producing", "running_fine", "back_online"):
            if any(kw in note_text for kw in ["shut in", "shut-in", "not producing", "down for"]):
                conflicts.append({
                    "type": "contradicts_other_note",
                    "detail": f"{author_name} noted: \"{note['text']}\" ({note_id})",
                    "evidence_id": note_id,
                    "other_user": author_name,
                })

        elif norm_state in ("not_producing", "shut_in", "down"):
            if any(kw in note_text for kw in ["running fine", "back online", "producing", "operational"]):
                conflicts.append({
                    "type": "contradicts_other_note",
                    "detail": f"{author_name} noted: \"{note['text']}\" ({note_id})",
                    "evidence_id": note_id,
                    "other_user": author_name,
                })

    # Also check ledger for claims and well_facts by other users
    cursor.execute("""
        SELECT entry_id, payload_json, user_id, reason, created_at, entry_type
        FROM ledger
        WHERE scope_id = ?
          AND entry_type IN ('claim', 'well_fact')
          AND user_id != ?
        ORDER BY created_at DESC
    """, (well_id, user_id))

    other_claims = cursor.fetchall()
    for claim in other_claims:
        payload = json.loads(claim["payload_json"])
        claim_state = payload.get("asserted_state", "").lower()
        note_text = (payload.get("text") or claim["reason"] or "").lower()

        # Deduce state from text if well_fact
        if not claim_state:
            if any(kw in note_text for kw in ["shut in", "shut-in", "not producing", "down for", "workover"]):
                claim_state = "shut_in"
            elif any(kw in note_text for kw in ["running fine", "back online", "producing", "operational"]):
                claim_state = "producing"

        claim_user = claim["user_id"]

        # Resolve user name
        cursor.execute("SELECT name FROM users WHERE user_id = ?", (claim_user,))
        u_row = cursor.fetchone()
        claim_author = u_row["name"] if u_row else claim_user
        citations.append(claim["entry_id"])

        summary_text = payload.get("text") or f"well is '{claim_state}'"

        if norm_state in ("producing", "running_fine", "back_online") and \
           claim_state in ("not_producing", "shut_in", "down"):
            conflicts.append({
                "type": "contradicts_other_note",
                "detail": f"{claim_author} noted: \"{summary_text}\" ({claim['entry_id']})",
                "evidence_id": claim["entry_id"],
                "other_user": claim_author,
            })
        elif norm_state in ("not_producing", "shut_in", "down") and \
             claim_state in ("producing", "running_fine", "back_online"):
            conflicts.append({
                "type": "contradicts_other_note",
                "detail": f"{claim_author} noted: \"{summary_text}\" ({claim['entry_id']})",
                "evidence_id": claim["entry_id"],
                "other_user": claim_author,
            })

    # ── Determine verdict ──

    has_data_conflict = any(c["type"] == "contradicts_data" for c in conflicts)
    has_note_conflict = any(c["type"] == "contradicts_other_note" for c in conflicts)

    if has_note_conflict:
        verdict = "contradicts_other_note"
    elif has_data_conflict:
        verdict = "contradicts_data"
    else:
        verdict = "consistent"

    return {
        "verdict": verdict,
        "well_id": well_id,
        "asserted_state": asserted_state,
        "user_id": user_id,
        "is_producing_per_data": is_producing,
        "inspector_note": inspector_note,
        "citations": list(set(citations)),
        "conflicts": conflicts,
    }


def check_correction_conflicts(
    conn: sqlite3.Connection,
    inspection_id: str,
    corrected_fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    After a raw/analysis correction, check if the correction conflicts with
    inspector notes or other observations on the same inspection.

    Returns conflict details with citations.
    """
    cursor = conn.cursor()

    # Get the inspection's existing data
    cursor.execute("""
        SELECT i.*, a.well_type
        FROM inspections i
        JOIN assets a ON i.asset_id = a.asset_id
        WHERE i.inspection_id = ?
    """, (inspection_id,))
    insp = cursor.fetchone()

    if not insp:
        return {"has_conflict": False, "conflicts": []}

    insp_data = dict(insp)
    conflicts: List[Dict[str, Any]] = []
    citations: List[str] = [inspection_id]

    # Check if inspector notes conflict with the correction
    if insp_data.get("notes"):
        inspector_note = insp_data["notes"]
        note_lower = inspector_note.lower()

        # If correcting wellhead temp to make well "producing" but inspector says "not moving"
        if "corrected_wellhead_temp" in corrected_fields:
            new_temp = corrected_fields["corrected_wellhead_temp"]
            ambient = insp_data.get("ambient_temp_c", 0)
            delta = new_temp - ambient if ambient else 0

            # Get threshold for this well type
            from backend.copilot.domain.effective import get_threshold_map
            thresholds = get_threshold_map()
            threshold = thresholds.get(insp_data["well_type"], 15.0)

            if delta >= threshold:
                # Correction says producing
                if any(kw in note_lower for kw in ["not moving", "stopped", "not running", "shut in", "not producing"]):
                    conflicts.append({
                        "type": "inspector_note_conflicts",
                        "detail": f"Inspector noted: \"{inspector_note}\"",
                        "new_value": f"Corrected temp ({new_temp} °C) suggests producing (delta {round(delta, 1)} °C ≥ {threshold} °C threshold)",
                        "evidence_id": inspection_id,
                    })

    # Check context notes that might conflict
    cursor.execute("""
        SELECT note_id, text, author_user_id, u.name as author_name
        FROM context_notes cn
        LEFT JOIN users u ON cn.author_user_id = u.user_id
        WHERE cn.inspection_id = ?
          AND cn.note_type != 'correction'
    """, (inspection_id,))

    for note in cursor.fetchall():
        citations.append(note["note_id"])

    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": conflicts,
        "citations": citations,
        "inspector_note": insp_data.get("notes"),
    }


def check_spill_disagreement(
    conn: sqlite3.Connection,
    inspection_id: str,
) -> Dict[str, Any]:
    """
    Check for conflicting views on whether a spill detection is real.
    Returns details of any disagreement between notes on the same inspection.
    """
    cursor = conn.cursor()

    # Get the inspection
    cursor.execute("""
        SELECT i.inspection_id, i.asset_id, i.notes, i.spill_detected,
               i.spill_est_volume_bbl, i.inspected_date
        FROM inspections i
        WHERE i.inspection_id = ?
    """, (inspection_id,))
    insp = cursor.fetchone()

    if not insp:
        return {"has_disagreement": False, "notes": []}

    asset_id = insp["asset_id"]

    # Get all context notes for this inspection/well around this date
    cursor.execute("""
        SELECT cn.note_id, cn.text, cn.author_user_id, u.name as author_name,
               cn.note_type, cn.created_at
        FROM context_notes cn
        LEFT JOIN users u ON cn.author_user_id = u.user_id
        WHERE cn.asset_id = ?
          AND (cn.inspection_id = ? OR cn.inspection_id IS NULL)
        ORDER BY cn.created_at ASC
    """, (asset_id, inspection_id))

    notes = [dict(n) for n in cursor.fetchall()]
    disagree_notes: List[Dict[str, Any]] = []

    for note in notes:
        text_lower = note["text"].lower()
        is_positive = any(kw in text_lower for kw in ["confirmed crude", "confirmed oil", "is crude", "real oil", "is real"])
        is_negative = any(kw in text_lower for kw in [
            "produced water", "not crude", "not oil", "not a spill", "rainwater",
            "water not crude", "water, not crude"
        ])

        if is_positive or is_negative:
            disagree_notes.append({
                **note,
                "position": "spill_is_real" if is_positive else "spill_is_not_real",
            })

    # Check if there are disagreeing notes
    positions = set(n["position"] for n in disagree_notes)
    has_disagreement = len(positions) > 1

    # Check if there's a maintenance repair (supports spill being real)
    cursor.execute("""
        SELECT maintenance_id FROM maintenance
        WHERE triggered_by_inspection_id = ?
    """, (inspection_id,))
    repair = cursor.fetchone()
    repair_done = repair is not None
    repair_id = repair["maintenance_id"] if repair else None

    # Check for formal correction (overrides all)
    cursor.execute("""
        SELECT note_id, text FROM context_notes
        WHERE inspection_id = ? AND note_type = 'correction'
    """, (inspection_id,))
    formal_correction = cursor.fetchone()

    # Determine effective status
    if formal_correction:
        effective_is_real = False  # Correction overrides
    else:
        effective_is_real = bool(insp["spill_detected"])  # Default stands

    return {
        "inspection_id": inspection_id,
        "has_disagreement": has_disagreement,
        "effective_is_real": effective_is_real,
        "repair_done": repair_done,
        "repair_id": repair_id,
        "formal_correction": dict(formal_correction) if formal_correction else None,
        "inspector_note": insp["notes"],
        "disagree_notes": disagree_notes,
        "citations": [inspection_id] + [n["note_id"] for n in disagree_notes] + ([repair_id] if repair_id else []),
    }
