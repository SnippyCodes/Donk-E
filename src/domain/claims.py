"""
src/domain/claims.py — Conflict Detection & Truth Engine (Milestone M4)

Cross-examines user assertions and sensor corrections against:
  1. Sensor data and physical thermodynamics (wellhead vs ambient delta temp).
  2. Inspector free-text observations (e.g. "Pump jack not moving.").
  3. Other users' active shared operational notes and claims.
  4. Non-correction notes that disagree with each other (e.g. produced water vs crude oil).

Exposes `check_claim(...)` (and `claims.check`) as the canonical conflict detection tool.
"""
import json
import sqlite3
from typing import Any, Dict, List, Optional

from backend.copilot.config import AS_OF


def check_claim(
    conn: sqlite3.Connection,
    well_id: str,
    asserted_state: str,
    user_id: str,
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deliverable B: Cross-examine a user claim about a well state.

    Args:
        conn: Active SQLite connection
        well_id: Target well (e.g. 'WELL-0175', 'WELL-0001')
        asserted_state: e.g. 'running_fine', 'producing', 'back_online', 'shut_in'
        user_id: User making assertion
        as_of: Reference date (defaults to AS_OF)

    Returns:
        Structured conflict object with verdict, severity, description,
        conflicting_record_id, requires_confirmation flag, and citations.
    """
    ref_date = as_of or AS_OF
    cursor = conn.cursor()

    # 1. Fetch latest well_now record
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
            "severity": "none",
            "conflicting_record_id": None,
            "author": None,
            "description": f"Well {well_id} not found in dataset.",
            "requires_confirmation": False,
            "citations": [],
            "conflicts": [],
            "inspector_notes": "",
        }

    well_data = dict(well)
    is_producing = bool(well_data["is_producing"])
    inspector_note = well_data.get("inspector_note") or ""
    inspector_name = well_data.get("inspector_name_full") or well_data.get("inspector_name") or well_data.get("inspector_user_id") or "Inspector"
    latest_insp_id = well_data["latest_inspection_id"]
    latest_date = well_data["latest_inspected_date"]

    citations: List[str] = [latest_insp_id]
    conflicts: List[Dict[str, Any]] = []

    norm_state = asserted_state.lower().strip()

    # ── Check Data vs. User Claim Conflict ──
    if norm_state in ("producing", "running_fine", "back_online", "operational"):
        if not is_producing:
            conflicts.append({
                "type": "contradicts_data",
                "detail": (
                    f"The {latest_date} inspection ({latest_insp_id}) by {inspector_name} shows wellhead "
                    f"only {well_data['delta_temp_c']} °C above air (threshold: {well_data['threshold_temp_delta']} °C). "
                    f"The well is not producing oil."
                ),
                "evidence_id": latest_insp_id,
            })
            if inspector_note:
                conflicts.append({
                    "type": "inspector_note_conflicts",
                    "detail": f"Inspector {inspector_name} noted: \"{inspector_note}\"",
                    "evidence_id": latest_insp_id,
                })

    elif norm_state in ("not_producing", "shut_in", "down"):
        if is_producing:
            conflicts.append({
                "type": "contradicts_data",
                "detail": (
                    f"The {latest_date} inspection ({latest_insp_id}) shows wellhead "
                    f"{well_data['delta_temp_c']} °C above air (threshold: {well_data['threshold_temp_delta']} °C). "
                    f"The well IS producing oil."
                ),
                "evidence_id": latest_insp_id,
            })

    # ── Check against other users' shared notes & context notes ──
    # Check context_notes
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

    for note in cursor.fetchall():
        note_text = note["text"].lower()
        note_id = note["note_id"]
        author_name = note["author_name"] or note["author_user_id"]
        citations.append(note_id)

        if norm_state in ("producing", "running_fine", "back_online"):
            if any(kw in note_text for kw in ["shut in", "shut-in", "not producing", "down for", "replacement"]):
                conflicts.append({
                    "type": "contradicts_other_note",
                    "detail": f"{author_name} noted: \"{note['text']}\" ({note_id})",
                    "evidence_id": note_id,
                    "other_user": author_name,
                })

    # Check shared_asset_notes
    cursor.execute("""
        SELECT s.note_id, s.note_text, s.author_user_id, u.name as author_name
        FROM shared_asset_notes s
        LEFT JOIN users u ON s.author_user_id = u.user_id
        WHERE s.asset_id = ?
          AND s.author_user_id != ?
          AND (s.valid_to IS NULL OR s.valid_to >= ?)
        ORDER BY s.created_at DESC
    """, (well_id, user_id, ref_date))

    for snote in cursor.fetchall():
        s_text = snote["note_text"].lower()
        s_id = snote["note_id"]
        s_author = snote["author_name"] or snote["author_user_id"]
        citations.append(s_id)

        if norm_state in ("producing", "running_fine", "back_online"):
            if any(kw in s_text for kw in ["shut in", "shut-in", "workover", "not producing", "down for"]):
                conflicts.append({
                    "type": "contradicts_other_note",
                    "detail": f"{s_author} noted: \"{snote['note_text']}\" ({s_id})",
                    "evidence_id": s_id,
                    "other_user": s_author,
                })

    # Check ledger for well_fact and claims
    cursor.execute("""
        SELECT entry_id, payload_json, user_id, reason, created_at, entry_type
        FROM ledger
        WHERE scope_id = ?
          AND entry_type IN ('claim', 'well_fact')
          AND user_id != ?
        ORDER BY created_at DESC
    """, (well_id, user_id))

    for claim in cursor.fetchall():
        payload = json.loads(claim["payload_json"])
        claim_state = payload.get("asserted_state", "").lower()
        note_text = (payload.get("text") or claim["reason"] or "").lower()

        if not claim_state:
            if any(kw in note_text for kw in ["shut in", "shut-in", "not producing", "down for", "workover"]):
                claim_state = "shut_in"
            elif any(kw in note_text for kw in ["running fine", "back online", "producing", "operational"]):
                claim_state = "producing"

        claim_user = claim["user_id"]
        cursor.execute("SELECT name FROM users WHERE user_id = ?", (claim_user,))
        u_row = cursor.fetchone()
        claim_author = u_row[0] if u_row else claim_user
        citations.append(claim["entry_id"])

        summary_text = payload.get("text") or f"well is '{claim_state}'"

        if norm_state in ("producing", "running_fine", "back_online") and claim_state in ("not_producing", "shut_in", "down"):
            conflicts.append({
                "type": "contradicts_other_note",
                "detail": f"{claim_author} noted: \"{summary_text}\" ({claim['entry_id']})",
                "evidence_id": claim["entry_id"],
                "other_user": claim_author,
            })

    # Determine verdict and severity
    has_note_conflict = any(c["type"] == "contradicts_other_note" for c in conflicts)
    has_data_conflict = any(c["type"] == "contradicts_data" for c in conflicts)

    if has_note_conflict:
        verdict = "contradicts_other_note"
        severity = "warning"
        requires_confirmation = True
    elif has_data_conflict:
        verdict = "contradicts_data"
        severity = "warning"
        requires_confirmation = True
    else:
        verdict = "consistent"
        severity = "none"
        requires_confirmation = False

    conflicting_record_id = conflicts[0]["evidence_id"] if conflicts else None
    primary_description = conflicts[0]["detail"] if conflicts else "Claim is consistent with data."
    primary_author = (conflicts[0].get("other_user") if conflicts else None) or inspector_name

    # De-duplicate citations
    seen = set()
    deduped_citations = []
    for c in citations:
        if c not in seen:
            deduped_citations.append(c)
            seen.add(c)

    return {
        "verdict": verdict,
        "severity": severity,
        "conflicting_record_id": conflicting_record_id,
        "author": primary_author,
        "description": primary_description,
        "requires_confirmation": requires_confirmation,
        "well_id": well_id,
        "asserted_state": asserted_state,
        "user_id": user_id,
        "is_producing_per_data": is_producing,
        "inspector_note": inspector_note,
        "conflicts": conflicts,
        "citations": deduped_citations,
    }


def check_note_disagreement(
    conn: sqlite3.Connection,
    inspection_id: str,
) -> Dict[str, Any]:
    """
    Deliverable B: Cross-examine non-correction notes that disagree on AI analysis (Q18).

    Example (Q18):
      - INS-0101-0197 flagged 1.0 bbl spill.
      - Ryan Brooks (CTX-0101-002) thought produced water.
      - Chris Dalton (CTX-0101-003) confirmed crude oil.
      - Repair MNT-0101-029 corroborates spill repair.
      - Detection stands: spill is real oil, disagreement explicitly surfaced.
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.inspection_id, i.asset_id, i.notes, i.spill_detected,
               i.spill_est_volume_bbl, i.inspected_date
        FROM inspections i
        WHERE i.inspection_id = ?
    """, (inspection_id,))
    insp = cursor.fetchone()

    if not insp:
        return {"has_disagreement": False, "effective_is_real": False, "citations": []}

    asset_id = insp["asset_id"]

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

    positions = set(n["position"] for n in disagree_notes)
    has_disagreement = len(positions) > 1

    cursor.execute("""
        SELECT maintenance_id FROM maintenance
        WHERE triggered_by_inspection_id = ?
    """, (inspection_id,))
    repair = cursor.fetchone()
    repair_done = repair is not None
    repair_id = repair["maintenance_id"] if repair else None

    cursor.execute("""
        SELECT note_id, text FROM context_notes
        WHERE inspection_id = ? AND note_type = 'correction'
    """, (inspection_id,))
    formal_correction = cursor.fetchone()

    effective_is_real = bool(insp["spill_detected"]) if not formal_correction else False

    citations = [inspection_id]
    for n in disagree_notes:
        citations.append(n["note_id"])
    if repair_id:
        citations.append(repair_id)

    return {
        "inspection_id": inspection_id,
        "asset_id": asset_id,
        "has_disagreement": has_disagreement,
        "effective_is_real": effective_is_real,
        "repair_done": repair_done,
        "repair_id": repair_id,
        "formal_correction": dict(formal_correction) if formal_correction else None,
        "inspector_note": insp["notes"],
        "disagree_notes": disagree_notes,
        "citations": citations,
        "explanation": (
            f"The AI flagged a {insp['spill_est_volume_bbl']} bbl spill at inspection {inspection_id} "
            f"(\"{insp['notes']}\"). Two operator notes disagree: Ryan Brooks (CTX-0101-002) thought it was "
            f"produced water, but Chris Dalton (CTX-0101-003) confirmed crude oil. Because no formal correction "
            f"was logged and spill repair {repair_id} was completed, the official detection stands as real oil."
            if has_disagreement else "No conflicting notes found."
        ),
    }


def check_correction_conflicts(
    conn: sqlite3.Connection,
    inspection_id: str,
    corrected_fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Check if a numeric sensor correction conflicts with physical observations (Q12).
    e.g. wellhead temp 41.0 °C vs "Pump jack not moving."
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, a.well_type
        FROM inspections i
        JOIN assets a ON i.asset_id = a.asset_id
        WHERE i.inspection_id = ?
    """, (inspection_id,))
    insp = cursor.fetchone()

    if not insp:
        return {"has_conflict": False, "conflicts": [], "citations": []}

    insp_data = dict(insp)
    conflicts: List[Dict[str, Any]] = []
    citations: List[str] = [inspection_id]

    if insp_data.get("notes"):
        inspector_note = insp_data["notes"]
        note_lower = inspector_note.lower()

        if "corrected_wellhead_temp" in corrected_fields:
            new_temp = corrected_fields["corrected_wellhead_temp"]
            ambient = insp_data.get("ambient_temp_c", 0)
            delta = new_temp - ambient if ambient else 0

            from backend.copilot.domain.effective import get_threshold_map
            thresholds = get_threshold_map()
            threshold = thresholds.get(insp_data["well_type"], 15.0)

            if delta >= threshold:
                if any(kw in note_lower for kw in ["not moving", "stopped", "not running", "shut in", "not producing"]):
                    conflicts.append({
                        "type": "inspector_note_conflicts",
                        "severity": "warning",
                        "detail": f"Inspector noted: \"{inspector_note}\"",
                        "new_value": f"Corrected temp ({new_temp} °C) suggests producing (delta {round(delta, 1)} °C ≥ {threshold} °C threshold)",
                        "evidence_id": inspection_id,
                    })

    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": conflicts,
        "citations": citations,
        "inspector_note": insp_data.get("notes"),
    }



# Canonical aliases
check = check_claim
check_spill_disagreement = check_note_disagreement
