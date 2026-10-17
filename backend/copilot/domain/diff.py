import json
import sqlite3
from typing import Any, Dict, List, Optional

from backend.copilot.db import get_connection
from backend.copilot.ingest.rules import load_rules


def get_bitemporal_audit_diff(
    conn: Optional[sqlite3.Connection] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Produce a side-by-side Bi-Temporal State Diff comparing:
      - Layer 1: Ingested Ground Truth (Raw immutable sensors & base SOP rules)
      - Layer 2: Effective Runtime State (Append-only ledger overlays & corrections)

    Surfaces all inspection corrections, spill overrides, wellhead temperature adjustments,
    and rule overrides with operator authorship and verified citations.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        diff_entries: List[Dict[str, Any]] = []
        evidence_ids: List[str] = []

        # 1. Inspection-level corrections from eff_inspection & context_notes
        cursor.execute("""
            SELECT inspection_id, asset_id, raw_wellhead_temp_c, effective_wellhead_temp_c,
                   raw_spill_detected, effective_spill_detected, is_spill_corrected,
                   correction_note_id, correction_note_text
            FROM eff_inspection
            WHERE is_spill_corrected = 1 
               OR raw_wellhead_temp_c != effective_wellhead_temp_c
               OR raw_spill_detected != effective_spill_detected
            ORDER BY inspected_date DESC
            LIMIT ?
        """, (limit,))
        insp_corrections = cursor.fetchall()

        for ic in insp_corrections:
            insp_id = ic["inspection_id"]
            note_id = ic["correction_note_id"]
            author = "Operator"

            # Lookup author if note_id exists
            if note_id:
                cursor.execute("SELECT author_user_id FROM context_notes WHERE note_id = ?", (note_id,))
                a_row = cursor.fetchone()
                if a_row:
                    author = a_row[0]
                evidence_ids.append(note_id)

            evidence_ids.append(insp_id)

            # Spill correction diff
            if ic["is_spill_corrected"] or ic["raw_spill_detected"] != ic["effective_spill_detected"]:
                diff_entries.append({
                    "scope_type": "inspection",
                    "scope_id": insp_id,
                    "asset_id": ic["asset_id"],
                    "field_name": "spill_detected",
                    "raw_ingested_value": f"{ic['raw_spill_detected']} (False Positive)",
                    "effective_runtime_value": f"{ic['effective_spill_detected']} (Cleared)",
                    "author_user_id": author,
                    "citation_id": note_id or insp_id,
                    "reason": ic["correction_note_text"] or "False positive spill cleared",
                    "evidence_ids": [note_id, insp_id] if note_id else [insp_id],
                })

            # Temp correction diff
            if ic["raw_wellhead_temp_c"] != ic["effective_wellhead_temp_c"]:
                diff_entries.append({
                    "scope_type": "inspection",
                    "scope_id": insp_id,
                    "asset_id": ic["asset_id"],
                    "field_name": "wellhead_temp_c",
                    "raw_ingested_value": f"{ic['raw_wellhead_temp_c']} °C",
                    "effective_runtime_value": f"{ic['effective_wellhead_temp_c']} °C",
                    "author_user_id": author,
                    "citation_id": note_id or insp_id,
                    "reason": ic["correction_note_text"] or "Temperature calibration adjustment",
                    "evidence_ids": [note_id, insp_id] if note_id else [insp_id],
                })

        # 2. Runtime corrections recorded in runtime_corrections or ledger
        try:
            cursor.execute("""
                SELECT correction_id, inspection_id, field_name, original_value,
                       corrected_value, reason, author_user_id, created_at
                FROM runtime_corrections
                ORDER BY created_at DESC
            """)
            rc_rows = cursor.fetchall()
            for rc in rc_rows:
                cid = rc["correction_id"]
                iid = rc["inspection_id"]
                evidence_ids.append(cid)
                if iid:
                    evidence_ids.append(iid)
                diff_entries.append({
                    "scope_type": "inspection",
                    "scope_id": iid or cid,
                    "asset_id": iid,
                    "field_name": rc["field_name"],
                    "raw_ingested_value": str(rc["original_value"]),
                    "effective_runtime_value": str(rc["corrected_value"]),
                    "author_user_id": rc["author_user_id"],
                    "citation_id": cid,
                    "reason": rc["reason"],
                    "evidence_ids": [cid, iid] if iid else [cid],
                })
        except Exception:
            pass

        # 3. Well-type rule overrides
        base_rules = load_rules()
        try:
            cursor.execute("""
                SELECT override_id, well_type, param_name, override_value, author_user_id, reason, created_at
                FROM well_type_rule_overrides
                ORDER BY created_at DESC
            """)
            wto_rows = cursor.fetchall()
            for wto in wto_rows:
                oid = wto["override_id"]
                wtype = wto["well_type"]
                pname = wto["param_name"]
                evidence_ids.append(oid)
                # Find baseline rule value
                baseline_val = "3"
                for r in base_rules.get("well_type_rules", []):
                    if r.get("well_type") == wtype and r.get("param") == pname:
                        baseline_val = str(r.get("value"))
                        break

                diff_entries.append({
                    "scope_type": "well_type",
                    "scope_id": wtype,
                    "asset_id": wtype,
                    "field_name": pname,
                    "raw_ingested_value": f"{baseline_val} (Base Rule)",
                    "effective_runtime_value": f"{wto['override_value']} (Runtime Override)",
                    "author_user_id": wto["author_user_id"],
                    "citation_id": oid,
                    "reason": wto["reason"],
                    "evidence_ids": [oid],
                })
        except Exception:
            pass

        # 4. Ledger entries of type 'param_override' or 'correction'
        cursor.execute("""
            SELECT entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason
            FROM ledger
            WHERE entry_type IN ('param_override', 'correction', 'rule_override')
            ORDER BY created_at DESC
        """)
        ledger_rows = cursor.fetchall()
        for lr in ledger_rows:
            lid = lr["entry_id"]
            evidence_ids.append(lid)
            try:
                payload = json.loads(lr["payload_json"] or "{}")
            except Exception:
                payload = {}

            diff_entries.append({
                "scope_type": lr["scope_type"],
                "scope_id": lr["scope_id"],
                "asset_id": lr["scope_id"],
                "field_name": payload.get("field_name", payload.get("param_name", "parameter")),
                "raw_ingested_value": str(payload.get("original_value", "Baseline")),
                "effective_runtime_value": str(payload.get("corrected_value", payload.get("override_value", "Overridden"))),
                "author_user_id": lr["user_id"],
                "citation_id": lid,
                "reason": lr["reason"],
                "evidence_ids": [lid],
            })

        unique_evidence = sorted(list(set(evidence_ids)))

        # Build Generative UI Table
        table_rows = []
        for d in diff_entries[:20]:
            table_rows.append({
                "Scope Type": d["scope_type"].upper(),
                "Scope ID": d["scope_id"],
                "Field": d["field_name"],
                "Raw Ingested (L1)": str(d["raw_ingested_value"]),
                "Effective State (L2)": str(d["effective_runtime_value"]),
                "Author": d["author_user_id"],
                "Citation": f"[{d['citation_id']}]",
            })

        visual_block = {
            "block_type": "table",
            "title": "Bi-Temporal State Diff: Raw Sensors (L1) vs Ledger Overlay (L2)",
            "columns": ["Scope Type", "Scope ID", "Field", "Raw Ingested (L1)", "Effective State (L2)", "Author", "Citation"],
            "rows": table_rows,
        }

        return {
            "summary": {
                "total_diff_count": len(diff_entries),
                "inspection_corrections_count": len(insp_corrections),
                "layer_1_model": "Immutable Raw Data Store",
                "layer_2_model": "Append-Only Runtime Ledger Overlay",
            },
            "diff_entries": diff_entries,
            "evidence_ids": unique_evidence,
            "visual": visual_block,
        }

    finally:
        if close_conn:
            conn.close()
