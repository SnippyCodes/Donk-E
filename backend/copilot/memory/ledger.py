"""
ledger.py — Append-only feedback ledger with reactive state rebuild.

Supports entry_types:
  - raw_correction:       User corrects a raw inspection reading (temp, volume)
  - analysis_correction:  User corrects an AI-generated estimate (spill volume)
  - rule_override:        User overrides a rule parameter for a scope (well_type, well, fleet)
  - well_fact:            User records a fact about a well (e.g. planned shut-in)
  - claim:                User makes a claim about well state (e.g. "running fine")

Every ledger write bumps ledger_version and optionally triggers a derived-table rebuild.
"""
import datetime
import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from backend.copilot.db import get_connection
from backend.copilot.domain.effective import materialize_derived_tables


# Global monotonic version counter (in-memory; reset on process restart)
_ledger_version = 0


def get_ledger_version() -> int:
    """Return current ledger version."""
    return _ledger_version


def record_feedback(
    conn: sqlite3.Connection,
    user_id: str,
    entry_type: str,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
    reason: Optional[str] = None,
    rebuild_derived: bool = True,
) -> Dict[str, Any]:
    """
    Append a feedback entry to the ledger and optionally rebuild derived tables.

    Args:
        conn: Active SQLite connection
        user_id: The user who made this feedback (injected by server, never from LLM)
        entry_type: One of raw_correction, analysis_correction, rule_override, well_fact, claim
        scope_type: One of inspection, well, well_type, fleet
        scope_id: The entity ID this applies to (e.g. INS-0164-0205, WELL-0001, T350, fleet)
        payload: JSON-serializable dict with the correction details
        reason: Optional human-readable reason for the correction
        rebuild_derived: Whether to re-materialize derived tables after write

    Returns:
        Dict with entry_id, cascade_impact (before/after diff), and ledger_version.
    """
    global _ledger_version

    entry_id = f"LEDGER-{uuid.uuid4().hex[:12]}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    # Snapshot BEFORE state (for cascade_impact)
    before_snapshot = _snapshot_state(conn, entry_type, scope_type, scope_id, payload)

    # Write to ledger
    with conn:
        conn.execute("""
            INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, created_at, user_id, scope_type, scope_id, entry_type, json.dumps(payload), reason))

    # Apply the mutation side-effect
    _apply_entry(conn, entry_type, scope_type, scope_id, payload, user_id, entry_id, created_at)

    # Rebuild derived tables if requested
    if rebuild_derived:
        materialize_derived_tables(conn)

    # Snapshot AFTER state
    after_snapshot = _snapshot_state(conn, entry_type, scope_type, scope_id, payload)

    # Compute cascade diff
    cascade_impact = _compute_cascade_impact(before_snapshot, after_snapshot, entry_type, scope_id, payload)

    _ledger_version += 1

    return {
        "entry_id": entry_id,
        "created_at": created_at,
        "user_id": user_id,
        "entry_type": entry_type,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "cascade_impact": cascade_impact,
        "ledger_version": _ledger_version,
    }


def get_ledger_entries(
    conn: sqlite3.Connection,
    scope_type: Optional[str] = None,
    scope_id: Optional[str] = None,
    entry_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query ledger entries with optional filters."""
    query = "SELECT * FROM ledger WHERE 1=1"
    params: list = []

    if scope_type:
        query += " AND scope_type = ?"
        params.append(scope_type)
    if scope_id:
        query += " AND scope_id = ?"
        params.append(scope_id)
    if entry_type:
        query += " AND entry_type = ?"
        params.append(entry_type)
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor = conn.cursor()
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


# ─────────────────────── Internal Helpers ───────────────────────


def _apply_entry(
    conn: sqlite3.Connection,
    entry_type: str,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
    user_id: str,
    entry_id: str,
    created_at: str,
) -> None:
    """Apply the side-effect of a ledger entry to raw/context tables."""

    if entry_type == "raw_correction":
        _apply_raw_correction(conn, scope_type, scope_id, payload, user_id, entry_id, created_at)
    elif entry_type == "analysis_correction":
        _apply_analysis_correction(conn, scope_type, scope_id, payload, user_id, entry_id, created_at)
    elif entry_type == "rule_override":
        _apply_rule_override(conn, scope_type, scope_id, payload, user_id, entry_id, created_at)
    elif entry_type == "well_fact":
        _apply_well_fact(conn, scope_type, scope_id, payload, user_id, entry_id, created_at)
    elif entry_type == "claim":
        # Claims are just recorded in ledger; no raw data mutation
        pass


def _apply_raw_correction(
    conn: sqlite3.Connection,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
    user_id: str,
    entry_id: str,
    created_at: str,
) -> None:
    """
    Rule 3: Raw tables are immutable. The raw correction is stored strictly
    in the ledger table and dynamically overlaid during derive table rebuild.
    """
    pass


def _apply_analysis_correction(
    conn: sqlite3.Connection,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
    user_id: str,
    entry_id: str,
    created_at: str,
) -> None:
    """
    Rule 3: Raw tables are immutable. The AI estimate correction is stored strictly
    in the ledger table and dynamically overlaid during derive table rebuild.
    """
    pass


def _apply_rule_override(
    conn: sqlite3.Connection,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
    user_id: str,
    entry_id: str,
    created_at: str,
) -> None:
    """
    Apply a rule parameter override. These are stored in the ledger itself
    and read by ParameterResolver during compliance evaluation.
    The ledger entry IS the override — no additional table mutation needed.
    """
    # The ledger entry with entry_type='rule_override' is already written.
    # ParameterResolver.get_param() queries the ledger for param_override entries.
    # We need to store the payload keyed by param name so ParameterResolver can find it.
    # Rewrite the ledger entry's payload as a param_override format.
    param = payload.get("param")
    new_value = payload.get("new_value")

    if param and new_value is not None:
        with conn:
            # Insert a param_override entry that ParameterResolver will find
            override_id = f"LEDGER-OVERRIDE-{uuid.uuid4().hex[:8]}"
            override_payload = json.dumps({param: new_value})
            conn.execute("""
                INSERT INTO ledger (entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason)
                VALUES (?, ?, ?, ?, ?, 'param_override', ?, ?)
            """, (override_id, created_at, user_id, scope_type, scope_id, override_payload,
                  f"Rule override by {user_id}: {param} = {new_value} (was {payload.get('original_value')})"))


def _apply_well_fact(
    conn: sqlite3.Connection,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
    user_id: str,
    entry_id: str,
    created_at: str,
) -> None:
    """
    Rule 3: Raw tables are immutable. The well fact is stored strictly in the ledger table
    with entry_type='well_fact'.
    """
    pass


# ─────────────────────── Snapshot / Cascade ───────────────────────


def _snapshot_state(
    conn: sqlite3.Connection,
    entry_type: str,
    scope_type: str,
    scope_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Take a snapshot of relevant state before/after a ledger write for cascade impact."""
    snapshot: Dict[str, Any] = {}
    cursor = conn.cursor()

    if entry_type in ("raw_correction", "analysis_correction"):
        insp_id = scope_id if scope_type == "inspection" else payload.get("inspection_id", scope_id)

        # Get asset_id
        cursor.execute("SELECT asset_id FROM inspections WHERE inspection_id = ?", (insp_id,))
        insp_row = cursor.fetchone()
        if insp_row:
            asset_id = insp_row[0]
            # Snapshot well_now status
            cursor.execute("SELECT is_producing, reason_type, reason_summary FROM well_now WHERE asset_id = ?", (asset_id,))
            wn = cursor.fetchone()
            if wn:
                snapshot["well_producing"] = bool(wn[0])
                snapshot["reason_type"] = wn[1]

            # Snapshot eff_inspection data for this inspection
            cursor.execute("""
                SELECT is_producing, effective_spill_detected, effective_spill_volume_bbl, is_spill_corrected
                FROM eff_inspection WHERE inspection_id = ?
            """, (insp_id,))
            ei = cursor.fetchone()
            if ei:
                snapshot["insp_producing"] = bool(ei[0])
                snapshot["spill_detected"] = bool(ei[1])
                snapshot["spill_volume"] = ei[2]

            # Snapshot spill reportable status
            cursor.execute("SELECT is_reportable FROM spills WHERE inspection_id = ?", (insp_id,))
            sp = cursor.fetchone()
            if sp:
                snapshot["spill_reportable"] = bool(sp[0])

    elif entry_type == "rule_override":
        # Snapshot affected wells' RCA status
        param = payload.get("param", "")
        if "rca" in param:
            well_type = scope_id if scope_type == "well_type" else None
            if well_type:
                cursor.execute("""
                    SELECT asset_id FROM assets WHERE well_type = ? AND area_id IN ('NE-07', 'NE-08')
                """, (well_type,))
                snapshot["affected_wells"] = [r[0] for r in cursor.fetchall()]

    return snapshot


def _compute_cascade_impact(
    before: Dict[str, Any],
    after: Dict[str, Any],
    entry_type: str,
    scope_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute a human-readable diff of cascading state changes."""
    impact: Dict[str, Any] = {}

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

    if "spill_volume" in before and "spill_volume" in after:
        if before.get("spill_volume") != after.get("spill_volume"):
            impact["volume_changed"] = {
                "before": before.get("spill_volume"),
                "after": after.get("spill_volume"),
            }

    return impact


def clear_ledger(conn: sqlite3.Connection, rebuild_derived: bool = True) -> None:
    """
    Clear all runtime ledger entries and user recall entries, restoring clean baseline.
    Rule 3: Raw tables were never modified, so derived tables are rebuilt strictly
    from pristine raw tables.
    """
    with conn:
        conn.execute("DELETE FROM ledger")
        conn.execute("DELETE FROM user_recall")
    if rebuild_derived:
        materialize_derived_tables(conn)
