"""
src/memory/ledger.py — Append-Only Runtime Ledger & Shared Fleet Memory (Milestone M4)

Level-1 Shared Fleet & Well Knowledge layer in SQLite (WAL mode):
  - runtime_corrections: Append-only numeric & categorical field overrides submitted at runtime.
  - well_type_rule_overrides: Well-type scoped policy overrides (strict well-type isolation).
  - shared_asset_notes: Global operational updates visible across users.
  - ledger: Unified append-only audit trail.

All mutations preserve Rule 3 (Immutable Raw Data). Derived tables (eff_inspection,
well_now, spills) are non-destructively overlaid.
"""
import datetime
import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.copilot.config import AS_OF
from backend.copilot.db import get_connection
from backend.copilot.domain.effective import materialize_derived_tables


def record_runtime_correction(
    conn: sqlite3.Connection,
    target_type: str,
    target_id: str,
    asset_id: str,
    field_name: str,
    original_value: Any,
    corrected_value: Any,
    author_user_id: str,
    reason: Optional[str] = None,
    status: str = "confirmed",
    rebuild_derived: bool = True,
) -> Dict[str, Any]:
    """
    Record an append-only runtime field correction (Q12, Q13, Q15).

    Args:
        conn: Active SQLite connection
        target_type: 'inspection', 'spill', 'asset'
        target_id: e.g. 'INS-0164-0205'
        asset_id: e.g. 'WELL-0164'
        field_name: 'wellhead_temp_c', 'spill_volume_bbl', 'spill_detected'
        original_value: Pre-correction value
        corrected_value: New effective value
        author_user_id: User making correction
        reason: Justification
        status: 'confirmed' or 'unconfirmed'
        rebuild_derived: Whether to trigger immediate derived table rebuild

    Returns:
        Structured record with correction_id, cascade_impact diff, and citations.
    """
    # Generate sequential or unique COR-ID
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM runtime_corrections")
    cnt = cursor.fetchone()[0] + 1
    correction_id = f"COR-{cnt:04d}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    # Snapshot state BEFORE
    before_snapshot = _snapshot_well_and_inspection(conn, target_id, asset_id)

    with conn:
        conn.execute("""
            INSERT INTO runtime_corrections (
                correction_id, target_type, target_id, asset_id, field_name,
                original_value, corrected_value, author_user_id, reason, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            correction_id, target_type, target_id, asset_id, field_name,
            float(original_value) if original_value is not None else None,
            float(corrected_value) if corrected_value is not None else None,
            author_user_id, reason, status, created_at
        ))

        # Also mirror to unified ledger
        ledger_entry_id = f"LEDGER-{correction_id}"
        payload = {
            "correction_id": correction_id,
            "target_type": target_type,
            "target_id": target_id,
            "asset_id": asset_id,
            "field_name": field_name,
            "original_value": original_value,
            "corrected_value": corrected_value,
            "reason": reason,
        }
        conn.execute("""
            INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
            VALUES (?, ?, ?, 'inspection', ?, 'raw_correction', ?, ?)
        """, (ledger_entry_id, created_at, author_user_id, target_id, json.dumps(payload), reason))

    # Rebuild derived views
    if rebuild_derived:
        materialize_derived_tables(conn)

    # Snapshot state AFTER
    after_snapshot = _snapshot_well_and_inspection(conn, target_id, asset_id)
    cascade_impact = _compute_cascade_impact(before_snapshot, after_snapshot, field_name, original_value, corrected_value)

    citations = [correction_id, target_id, asset_id]
    if before_snapshot.get("inspector_note"):
        citations.append(f"INSP_NOTE:{target_id}")

    return {
        "correction_id": correction_id,
        "target_id": target_id,
        "asset_id": asset_id,
        "field_name": field_name,
        "original_value": original_value,
        "corrected_value": corrected_value,
        "author_user_id": author_user_id,
        "status": status,
        "created_at": created_at,
        "cascade_impact": cascade_impact,
        "citations": citations,
    }


def record_rule_override(
    conn: sqlite3.Connection,
    well_type: str,
    rule_field: str,
    new_value: Any,
    author_user_id: str,
    original_value: Any = None,
    equipment_kind: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record an append-only well-type rule override (Q14).
    Enforces strict well-type scope isolation (T350 does NOT affect T200).
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM well_type_rule_overrides")
    cnt = cursor.fetchone()[0] + 1
    override_id = f"OVR-{cnt:04d}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    val_float = float(new_value)
    orig_float = float(original_value) if original_value is not None else None

    with conn:
        conn.execute("""
            INSERT INTO well_type_rule_overrides (
                override_id, well_type, rule_field, equipment_kind,
                original_value, new_value, author_user_id, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            override_id, well_type, rule_field, equipment_kind,
            orig_float, val_float, author_user_id, reason, created_at
        ))

        # Mirror to unified ledger
        ledger_entry_id = f"LEDGER-{override_id}"
        payload = {
            "override_id": override_id,
            "param": rule_field,
            "equipment_kind": equipment_kind,
            "new_value": val_float,
            "original_value": orig_float,
        }
        conn.execute("""
            INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
            VALUES (?, ?, ?, 'well_type', ?, 'rule_override', ?, ?)
        """, (ledger_entry_id, created_at, author_user_id, well_type, json.dumps(payload), reason))

        # Also insert param_override format for ParameterResolver
        conn.execute("""
            INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
            VALUES (?, ?, ?, 'well_type', ?, 'param_override', ?, ?)
        """, (f"LEDGER-PARAM-{override_id}", created_at, author_user_id, well_type,
              json.dumps({rule_field: val_float}), reason))

    citations = [override_id, f"MANUAL:{well_type}"]
    return {
        "override_id": override_id,
        "well_type": well_type,
        "rule_field": rule_field,
        "equipment_kind": equipment_kind,
        "original_value": original_value,
        "new_value": new_value,
        "author_user_id": author_user_id,
        "created_at": created_at,
        "citations": citations,
    }


def record_shared_asset_note(
    conn: sqlite3.Connection,
    asset_id: str,
    author_user_id: str,
    note_text: str,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    reason: Optional[str] = None,
    rebuild_derived: bool = True,
) -> Dict[str, Any]:
    """
    Record a shared operational note visible across all users (Q16).
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM shared_asset_notes")
    cnt = cursor.fetchone()[0] + 1
    note_id = f"SAN-{cnt:04d}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    with conn:
        conn.execute("""
            INSERT INTO shared_asset_notes (
                note_id, asset_id, author_user_id, note_text, valid_from, valid_to, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?)
        """, (note_id, asset_id, author_user_id, note_text, valid_from, valid_to, created_at))

        # Mirror to unified ledger
        ledger_entry_id = f"LEDGER-{note_id}"
        payload = {
            "note_id": note_id,
            "text": note_text,
            "note_type": "operational",
            "valid_from": valid_from,
            "valid_to": valid_to,
        }
        conn.execute("""
            INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
            VALUES (?, ?, ?, 'well', ?, 'well_fact', ?, ?)
        """, (ledger_entry_id, created_at, author_user_id, asset_id, json.dumps(payload), reason or note_text))

    if rebuild_derived:
        materialize_derived_tables(conn)

    citations = [note_id, asset_id]
    return {
        "note_id": note_id,
        "asset_id": asset_id,
        "author_user_id": author_user_id,
        "note_text": note_text,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "created_at": created_at,
        "citations": citations,
    }


def get_runtime_corrections(
    conn: sqlite3.Connection,
    target_id: Optional[str] = None,
    asset_id: Optional[str] = None,
    field_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query confirmed runtime corrections with filters."""
    query = "SELECT * FROM runtime_corrections WHERE status = 'confirmed'"
    params: list = []
    if target_id:
        query += " AND target_id = ?"
        params.append(target_id)
    if asset_id:
        query += " AND asset_id = ?"
        params.append(asset_id)
    if field_name:
        query += " AND field_name = ?"
        params.append(field_name)

    query += " ORDER BY created_at DESC"
    cursor = conn.cursor()
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]


def clear_runtime_memory(conn: sqlite3.Connection, rebuild_derived: bool = True) -> None:
    """Clear all M4 runtime tables and restore clean baseline state."""
    with conn:
        conn.execute("DELETE FROM runtime_corrections")
        conn.execute("DELETE FROM well_type_rule_overrides")
        conn.execute("DELETE FROM shared_asset_notes")
        conn.execute("DELETE FROM user_sessions")
        conn.execute("DELETE FROM user_messages")
        conn.execute("DELETE FROM ledger")
        conn.execute("DELETE FROM user_recall")
    if rebuild_derived:
        materialize_derived_tables(conn)


# ─────────────────────── Internal Helpers ───────────────────────


def _snapshot_well_and_inspection(
    conn: sqlite3.Connection,
    inspection_id: str,
    asset_id: str,
) -> Dict[str, Any]:
    """Capture snapshot of well producing status, spill status, and inspector note."""
    snapshot: Dict[str, Any] = {}
    cursor = conn.cursor()

    cursor.execute("SELECT is_producing, wellhead_temp_c, inspector_note FROM well_now WHERE asset_id = ?", (asset_id,))
    row = cursor.fetchone()
    if row:
        snapshot["well_producing"] = bool(row[0])
        snapshot["wellhead_temp_c"] = row[1]
        snapshot["inspector_note"] = row[2]

    cursor.execute("SELECT effective_spill_detected, effective_spill_volume_bbl FROM eff_inspection WHERE inspection_id = ?", (inspection_id,))
    insp = cursor.fetchone()
    if insp:
        snapshot["spill_detected"] = bool(insp[0])
        snapshot["spill_volume_bbl"] = insp[1]
        snapshot["spill_reportable"] = (insp[1] is not None and insp[1] >= 5.0)

    return snapshot


def _compute_cascade_impact(
    before: Dict[str, Any],
    after: Dict[str, Any],
    field_name: str,
    orig_val: Any,
    corr_val: Any,
) -> Dict[str, Any]:
    """Compute cascade diff between before and after snapshots."""
    impact: Dict[str, Any] = {
        "field": field_name,
        "original_value": orig_val,
        "corrected_value": corr_val,
    }

    if "well_producing" in before and "well_producing" in after:
        if before["well_producing"] != after["well_producing"]:
            impact["producing_status_changed"] = {
                "before": before["well_producing"],
                "after": after["well_producing"],
            }

    if "spill_reportable" in before and "spill_reportable" in after:
        if before.get("spill_reportable") != after.get("spill_reportable"):
            impact["reportable_status_changed"] = {
                "before": before.get("spill_reportable", False),
                "after": after.get("spill_reportable", False),
            }

    if before.get("inspector_note"):
        impact["inspector_note"] = before["inspector_note"]

    return impact
