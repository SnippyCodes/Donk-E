import json
import sqlite3
from typing import Any, Dict, List, Optional
from backend.copilot.db import get_connection
from backend.copilot.ingest.rules import load_rules


class ParameterResolver:
    """
    Hierarchical parameter resolver implementing strict scope discipline.
    Resolution order:
      1. Inspection-level override (ledger)
      2. Well-level override (ledger)
      3. Well-type override (ledger -> rules.yaml)
      4. Fleet-level default (ledger -> rules.yaml)
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn
        self._rules_data = load_rules()

    def get_param(
        self,
        param_name: str,
        well_id: Optional[str] = None,
        well_type: Optional[str] = None,
        inspection_id: Optional[str] = None,
        default: Any = None,
    ) -> Dict[str, Any]:
        """Resolve effective parameter value and metadata given scope context."""
        # Auto-detect well_type if well_id provided
        if well_id and not well_type and self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT well_type FROM assets WHERE asset_id = ?", (well_id,))
            row = cursor.fetchone()
            if row:
                well_type = row[0]

        # 1. Check ledger for runtime overrides (if conn available)
        if self.conn:
            cursor = self.conn.cursor()
            # Check inspection scope
            if inspection_id:
                cursor.execute("""
                    SELECT payload_json FROM ledger
                    WHERE entry_type = 'param_override'
                      AND scope_type = 'inspection'
                      AND scope_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (inspection_id,))
                row = cursor.fetchone()
                if row:
                    payload = json.loads(row[0])
                    if param_name in payload:
                        return {"value": payload[param_name], "scope": "inspection", "scope_id": inspection_id}

            # Check well scope
            if well_id:
                cursor.execute("""
                    SELECT payload_json FROM ledger
                    WHERE entry_type = 'param_override'
                      AND scope_type = 'well'
                      AND scope_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (well_id,))
                row = cursor.fetchone()
                if row:
                    payload = json.loads(row[0])
                    if param_name in payload:
                        return {"value": payload[param_name], "scope": "well", "scope_id": well_id}

            # Check well_type scope in ledger
            if well_type:
                cursor.execute("""
                    SELECT payload_json FROM ledger
                    WHERE entry_type = 'param_override'
                      AND scope_type = 'well_type'
                      AND scope_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (well_type,))
                row = cursor.fetchone()
                if row:
                    payload = json.loads(row[0])
                    if param_name in payload:
                        return {"value": payload[param_name], "scope": "well_type", "scope_id": well_type}

            # Check fleet scope in ledger
            cursor.execute("""
                SELECT payload_json FROM ledger
                WHERE entry_type = 'param_override'
                  AND scope_type = 'fleet'
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                payload = json.loads(row[0])
                if param_name in payload:
                    return {"value": payload[param_name], "scope": "fleet", "scope_id": "fleet"}

        # 2. Check rules.yaml for well_type
        if well_type:
            for r in self._rules_data.get("rules", []):
                if r.get("param") == param_name and r.get("applies_to") == well_type:
                    return {
                        "value": r["value"],
                        "unit": r.get("unit"),
                        "scope": "well_type",
                        "scope_id": well_type,
                        "source_file": r.get("source_file"),
                        "source_section": r.get("source_section"),
                    }

        # 3. Check rules.yaml for fleet default
        for r in self._rules_data.get("rules", []):
            if r.get("param") == param_name and r.get("applies_to") == "fleet":
                return {
                    "value": r["value"],
                    "unit": r.get("unit"),
                    "scope": "fleet",
                    "scope_id": "fleet",
                    "source_file": r.get("source_file"),
                    "source_section": r.get("source_section"),
                }

        return {
            "value": default,
            "unit": None,
            "scope": "default",
            "scope_id": None,
        }
