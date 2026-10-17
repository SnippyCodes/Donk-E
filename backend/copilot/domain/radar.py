import datetime
import json
import re
import sqlite3
from typing import Any, Dict, List, Optional
from dateutil.relativedelta import relativedelta

from backend.copilot.db import get_connection
from backend.copilot.domain.params import ParameterResolver
from backend.copilot.resolver import get_data_end


def scan_proactive_fleet_risks(
    conn: Optional[sqlite3.Connection] = None,
    thermal_margin_deg: float = 2.5,
) -> Dict[str, Any]:
    """
    Deterministically scan the entire fleet for proactive operational risks:
      1. Thermal Margin Warnings: Producing wells whose effective temperature delta
         (delta_temp_c) is within thermal_margin_deg (default 2.5°C) of their well-type threshold
         (flagging them as 'At Risk of Stalling' with [INS-...] citations).
      2. Pre-RCA Threshold Watchlist: Wells with exactly (threshold - 1) corrective repairs
         on the same equipment kind in a 12-month window (one breakdown away from mandatory RCA).
      3. Stale Status & Unresolved Conflicts: Assets where recorded status contradicts production,
         plus contradictory operator notes (e.g. INS-0101-0197).
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        params = ParameterResolver(conn)
        data_end_str = get_data_end(conn)
        data_end_dt = datetime.date.fromisoformat(data_end_str)
        window_12m_start = (data_end_dt - relativedelta(years=1)).isoformat()

        evidence_ids: List[str] = []

        # 1. Thermal Margin Warnings
        cursor.execute("""
            SELECT asset_id, well_type, area_id, name, latest_inspection_id, latest_inspected_date,
                   ambient_temp_c, wellhead_temp_c, delta_temp_c, threshold_temp_delta, is_producing
            FROM well_now
            WHERE is_producing = 1
            ORDER BY (delta_temp_c - threshold_temp_delta) ASC
        """)
        thermal_rows = cursor.fetchall()
        thermal_warnings: List[Dict[str, Any]] = []

        for row in thermal_rows:
            delta = row["delta_temp_c"] or 0.0
            thresh = row["threshold_temp_delta"] or 15.0
            margin = round(delta - thresh, 2)
            if margin <= thermal_margin_deg or abs(margin) <= thermal_margin_deg:
                insp_id = row["latest_inspection_id"]
                if insp_id:
                    evidence_ids.append(insp_id)
                thermal_warnings.append({
                    "asset_id": row["asset_id"],
                    "well_type": row["well_type"],
                    "name": row["name"],
                    "delta_temp_c": delta,
                    "threshold_temp_delta": thresh,
                    "margin_c": margin,
                    "latest_inspection_id": insp_id,
                    "status": "At Risk of Stalling",
                    "evidence_ids": [insp_id] if insp_id else [],
                })

        # 2. Pre-RCA Threshold Watchlist (threshold - 1 corrective repairs in 12 months)
        cursor.execute("SELECT asset_id, well_type FROM assets")
        all_assets = cursor.fetchall()
        pre_rca_watchlist: List[Dict[str, Any]] = []

        for a in all_assets:
            w_id = a["asset_id"]
            w_type = a["well_type"]
            rca_thresh = params.get_param("rca_corrective_count", well_id=w_id, default=3)["value"]
            target_count = rca_thresh - 1

            if target_count < 1:
                continue

            cursor.execute("""
                SELECT equipment_kind, COUNT(*) as cnt, GROUP_CONCAT(maintenance_id, ', ') as mnt_ids
                FROM maintenance
                WHERE asset_id = ?
                  AND maintenance_type = 'corrective'
                  AND started_at >= ?
                  AND started_at <= ?
                GROUP BY equipment_kind
                HAVING cnt = ?
            """, (w_id, window_12m_start, f"{data_end_str}T23:59:59Z", target_count))
            rca_candidates = cursor.fetchall()

            for cand in rca_candidates:
                equip = cand["equipment_kind"]
                repairs = [m.strip() for m in cand["mnt_ids"].split(",") if m.strip()]
                evidence_ids.extend(repairs)
                pre_rca_watchlist.append({
                    "asset_id": w_id,
                    "well_type": w_type,
                    "equipment_kind": equip,
                    "corrective_repairs_count": cand["cnt"],
                    "rca_threshold": rca_thresh,
                    "repairs": repairs,
                    "warning": f"1 breakdown away from mandatory RCA ({cand['cnt']}/{rca_thresh} repairs)",
                    "evidence_ids": repairs,
                })

        # 3. Stale Status Wells
        cursor.execute("""
            SELECT asset_id, name, well_type, recorded_status, is_producing,
                   latest_inspection_id, reason_summary
            FROM well_now
            WHERE status_is_stale = 1
            ORDER BY asset_id ASC
        """)
        stale_rows = cursor.fetchall()
        stale_status_wells: List[Dict[str, Any]] = []
        for s in stale_rows:
            insp_id = s["latest_inspection_id"]
            if insp_id:
                evidence_ids.append(insp_id)
            stale_status_wells.append({
                "asset_id": s["asset_id"],
                "name": s["name"],
                "well_type": s["well_type"],
                "recorded_status": s["recorded_status"],
                "is_producing": bool(s["is_producing"]),
                "reason_summary": s["reason_summary"] or "No recorded work order",
                "latest_inspection_id": insp_id,
                "evidence_ids": [insp_id] if insp_id else [],
            })

        # 4. Unresolved Operator Disagreements & Conflicts (e.g. INS-0101-0197)
        unresolved_conflicts: List[Dict[str, Any]] = []

        # Check multi-note contradictions on inspections
        cursor.execute("""
            SELECT note_id, asset_id, author_user_id, note_type, text
            FROM context_notes
        """)
        all_notes = cursor.fetchall()
        notes_by_insp: Dict[str, List[Dict[str, Any]]] = {}
        for n in all_notes:
            m = re.findall(r"INS-\d{4}-\d{4}", n["text"])
            for insp_id in m:
                notes_by_insp.setdefault(insp_id, []).append(dict(n))

        for insp_id, n_list in notes_by_insp.items():
            if len(n_list) > 1:
                c_evidence = [insp_id] + [n["note_id"] for n in n_list if n.get("note_id")]
                evidence_ids.extend(c_evidence)
                notes_summary = " vs ".join([f"[{n['note_id']}] ({n['author_user_id']}): \"{n['text']}\"" for n in n_list])
                unresolved_conflicts.append({
                    "inspection_id": insp_id,
                    "asset_id": n_list[0]["asset_id"],
                    "conflict_type": "contradictory_operator_notes",
                    "conflict_summary": f"Disagreement on {insp_id}: {notes_summary}",
                    "evidence_ids": c_evidence,
                })

        # Check explicit dispute / claim entries in ledger
        cursor.execute("""
            SELECT entry_id, user_id, scope_type, scope_id, entry_type, payload_json, reason
            FROM ledger
            WHERE entry_type IN ('claim', 'dispute')
            ORDER BY created_at DESC
        """)
        ledger_disputes = cursor.fetchall()
        for ld in ledger_disputes:
            lid = ld["entry_id"]
            evidence_ids.append(lid)
            unresolved_conflicts.append({
                "inspection_id": None,
                "asset_id": ld["scope_id"],
                "conflict_type": "ledger_claim_dispute",
                "conflict_summary": f"Operator {ld['user_id']} claim: {ld['reason']}",
                "evidence_ids": [lid],
            })

        unique_evidence = sorted(list(set(evidence_ids)))

        table_rows = []
        for tw in thermal_warnings[:5]:
            table_rows.append({
                "Asset ID": tw["asset_id"],
                "Category": "Thermal Margin",
                "Details": f"ΔTemp {tw['delta_temp_c']}°C (Margin: {tw['margin_c']}°C vs {tw['threshold_temp_delta']}°C threshold)",
                "Action": "At Risk of Stalling",
                "Evidence": " ".join([f"[{e}]" for e in tw["evidence_ids"]]),
            })
        for pr in pre_rca_watchlist[:5]:
            table_rows.append({
                "Asset ID": pr["asset_id"],
                "Category": "Pre-RCA Watchlist",
                "Details": f"{pr['equipment_kind']} has {pr['corrective_repairs_count']} repairs (Threshold: {pr['rca_threshold']})",
                "Action": "1 repair away from mandatory RCA",
                "Evidence": " ".join([f"[{e}]" for e in pr["evidence_ids"]]),
            })
        for ss in stale_status_wells[:5]:
            table_rows.append({
                "Asset ID": ss["asset_id"],
                "Category": "Stale Status",
                "Details": f"Recorded '{ss['recorded_status']}' but producing={ss['is_producing']}",
                "Action": "Requires Field Audit",
                "Evidence": " ".join([f"[{e}]" for e in ss["evidence_ids"]]),
            })
        for uc in unresolved_conflicts[:5]:
            table_rows.append({
                "Asset ID": uc["asset_id"],
                "Category": "Unresolved Conflict",
                "Details": uc["conflict_summary"][:80] + "...",
                "Action": "Reconcile Operator Testimony",
                "Evidence": " ".join([f"[{e}]" for e in uc["evidence_ids"]]),
            })

        visual_block = {
            "block_type": "table",
            "title": "⚡ Proactive Fleet Risk & Anomaly Radar",
            "columns": ["Asset ID", "Category", "Details", "Action", "Evidence"],
            "rows": table_rows,
        }

        total_alerts = len(thermal_warnings) + len(pre_rca_watchlist) + len(stale_status_wells) + len(unresolved_conflicts)
        risk_level = "ELEVATED" if total_alerts > 0 else "NOMINAL"

        return {
            "summary": {
                "thermal_margin_warnings_count": len(thermal_warnings),
                "pre_rca_watchlist_count": len(pre_rca_watchlist),
                "stale_status_wells_count": len(stale_status_wells),
                "unresolved_conflicts_count": len(unresolved_conflicts),
                "fleet_risk_level": risk_level,
                "data_end": data_end_str,
            },
            "thermal_warnings": thermal_warnings,
            "pre_rca_watchlist": pre_rca_watchlist,
            "stale_status_wells": stale_status_wells,
            "unresolved_conflicts": unresolved_conflicts,
            "evidence_ids": unique_evidence,
            "visual": visual_block,
        }

    finally:
        if close_conn:
            conn.close()
