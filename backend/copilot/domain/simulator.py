import datetime
import json
import re
import sqlite3
from typing import Any, Dict, List, Optional
from dateutil.relativedelta import relativedelta

from backend.copilot.db import get_connection
from backend.copilot.domain.params import ParameterResolver
from backend.copilot.resolver import get_data_end


def simulate_fleet_what_if(
    scenario_query: Optional[str] = None,
    scenario_type: Optional[str] = None,
    target_well_type: Optional[str] = None,
    simulated_value: Optional[float] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """
    Deterministically simulate counterfactual 'What-If' scenarios across the fleet
    without mutating the immutable SQLite tables or the append-only ledger.

    Supported Scenarios:
      1. 'spill_threshold': What if the reportable spill threshold (SR-01) changes?
         e.g., dropping from 5.0 bbl to 3.0 bbl.
      2. 'rca_threshold': What if the corrective repair threshold for mandatory RCA changes?
         e.g., T350 pumps drop from 3 to 2 repairs in 12 months.
      3. 'temp_threshold': What if the temperature delta threshold changes?
         e.g., T200 or T350 threshold increases by 3.0°C.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        params = ParameterResolver(conn)
        data_end_str = get_data_end(conn)

        # Baseline ledger count check to guarantee immutability
        cursor.execute("SELECT COUNT(*) FROM ledger")
        initial_ledger_count = cursor.fetchone()[0]

        # Natural language parsing if scenario_query provided
        q = (scenario_query or "").lower()
        if not scenario_type:
            if "spill" in q or "bbl" in q or "sr-01" in q:
                scenario_type = "spill_threshold"
            elif "rca" in q or "corrective" in q or "repair" in q:
                scenario_type = "rca_threshold"
            elif "temp" in q or "temperature" in q or "delta" in q or "stall" in q:
                scenario_type = "temp_threshold"
            else:
                scenario_type = "spill_threshold"

        evidence_ids: List[str] = []
        flipped_assets: List[Dict[str, Any]] = []

        # =====================================================================
        # SCENARIO 1: Spill Reportable Volume Threshold (SR-01)
        # =====================================================================
        if scenario_type == "spill_threshold":
            baseline_thresh = 5.0  # SOP SR-01 standard
            if simulated_value is None:
                # Look for target e.g. "to 3.0 bbl" or find all numbers and take the target/last
                m_to = re.search(r"(?:to|at|drop(?:s|ped)?\s+to|set\s+to)\s+(\d+(?:\.\d+)?)", q)
                if m_to:
                    simulated_thresh = float(m_to.group(1))
                else:
                    m_all = re.findall(r"(\d+(?:\.\d+)?)\s*bbl", q)
                    simulated_thresh = float(m_all[-1]) if m_all else 3.0
            else:
                simulated_thresh = float(simulated_value)

            cursor.execute("SELECT COUNT(*) FROM spills WHERE is_reportable = 1")
            before_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM spills WHERE volume_bbl >= ?", (simulated_thresh,))
            after_count = cursor.fetchone()[0]

            net_change = after_count - before_count

            # Find all flipped spills
            if simulated_thresh < baseline_thresh:
                cursor.execute("""
                    SELECT spill_id, asset_id, inspection_id, date, volume_bbl, is_reportable
                    FROM spills
                    WHERE volume_bbl >= ? AND volume_bbl < ?
                    ORDER BY volume_bbl DESC
                """, (simulated_thresh, baseline_thresh))
            else:
                cursor.execute("""
                    SELECT spill_id, asset_id, inspection_id, date, volume_bbl, is_reportable
                    FROM spills
                    WHERE volume_bbl >= ? AND volume_bbl < ?
                    ORDER BY volume_bbl DESC
                """, (baseline_thresh, simulated_thresh))

            flipped_rows = cursor.fetchall()
            for r in flipped_rows:
                s_id = r["spill_id"]
                insp_id = r["inspection_id"]
                if insp_id:
                    evidence_ids.append(insp_id)
                evidence_ids.append(s_id)
                flipped_assets.append({
                    "asset_id": r["asset_id"],
                    "record_id": s_id,
                    "date": r["date"],
                    "volume_bbl": r["volume_bbl"],
                    "before_status": "Non-Reportable (Compliant)",
                    "simulated_status": "Reportable Violation (SR-01 Breach)",
                    "evidence_ids": [s_id, insp_id] if insp_id else [s_id],
                })

            scenario_name = f"Spill Reportable Threshold: {baseline_thresh} bbl -> {simulated_thresh} bbl"
            param_changed = "spill_reportable_volume_bbl"
            baseline_val = baseline_thresh
            simulated_val = simulated_thresh
            y_axis_label = "Reportable Spill Violations"

        # =====================================================================
        # SCENARIO 2: RCA Corrective Repair Threshold
        # =====================================================================
        elif scenario_type == "rca_threshold":
            target_type = target_well_type or ("T350" if "t350" in q else ("T200" if "t200" in q else "T350"))
            baseline_val = 3
            simulated_val = int(simulated_value) if simulated_value is not None else 2

            window_start = (datetime.date.fromisoformat(data_end_str) - relativedelta(years=1)).isoformat()

            cursor.execute("SELECT asset_id FROM assets WHERE well_type = ?", (target_type,))
            target_wells = [r[0] for r in cursor.fetchall()]

            before_wells = set()
            after_wells = set()
            well_repair_map = {}

            for w in target_wells:
                cursor.execute("""
                    SELECT equipment_kind, COUNT(*) as cnt, GROUP_CONCAT(maintenance_id, ', ') as m_ids
                    FROM maintenance
                    WHERE asset_id = ?
                      AND maintenance_type = 'corrective'
                      AND started_at >= ?
                      AND started_at <= ?
                    GROUP BY equipment_kind
                """, (w, window_start, f"{data_end_str}T23:59:59Z"))
                for row in cursor.fetchall():
                    repairs = [m.strip() for m in row["m_ids"].split(",") if m.strip()]
                    if row["cnt"] >= baseline_val:
                        before_wells.add(w)
                    if row["cnt"] >= simulated_val:
                        after_wells.add(w)
                        well_repair_map[w] = {
                            "equipment": row["equipment_kind"],
                            "count": row["cnt"],
                            "repairs": repairs,
                        }

            before_count = len(before_wells)
            after_count = len(after_wells)
            net_change = after_count - before_count

            # Flipped wells are those in after_wells but not in before_wells
            for w in sorted(list(after_wells - before_wells)):
                info = well_repair_map[w]
                evidence_ids.extend(info["repairs"])
                flipped_assets.append({
                    "asset_id": w,
                    "record_id": f"{info['equipment']}_repairs",
                    "equipment": info["equipment"],
                    "repair_count": info["count"],
                    "before_status": f"Compliant (<{baseline_val} repairs)",
                    "simulated_status": f"Mandatory RCA Required (>= {simulated_val} repairs)",
                    "evidence_ids": info["repairs"],
                })

            scenario_name = f"RCA Corrective Threshold for {target_type}: {baseline_val} -> {simulated_val} Repairs"
            param_changed = "rca_corrective_count"
            y_axis_label = f"Wells Triggering Mandatory RCA ({target_type})"

        # =====================================================================
        # SCENARIO 3: Temperature Delta Stall Threshold
        # =====================================================================
        else:
            target_type = target_well_type or ("T200" if "t200" in q else "T350")
            cursor.execute("SELECT threshold_temp_delta FROM well_now WHERE well_type = ? LIMIT 1", (target_type,))
            row = cursor.fetchone()
            baseline_val = float(row[0]) if row and row[0] else (15.0 if target_type == "T200" else 20.0)

            if simulated_value is not None:
                simulated_val = float(simulated_value)
            else:
                m_by = re.search(r"(?:increased?|raised?|bumped?|plus|\+)\s*(?:by\s*)?(\d+(?:\.\d+)?)", q)
                m_to = re.search(r"(?:to|set\s+to|at)\s+(\d+(?:\.\d+)?)", q)
                if m_by:
                    delta_c = float(m_by.group(1))
                    simulated_val = baseline_val + delta_c
                elif m_to:
                    simulated_val = float(m_to.group(1))
                else:
                    m_num = re.search(r"(\d+(?:\.\d+)?)\s*(?:c|°c|deg)", q)
                    simulated_val = baseline_val + float(m_num.group(1)) if m_num else baseline_val + 3.0

            # Count producing wells under baseline vs simulated threshold
            cursor.execute("""
                SELECT asset_id, latest_inspection_id, delta_temp_c, is_producing
                FROM well_now
                WHERE well_type = ?
            """, (target_type,))
            wells = cursor.fetchall()

            before_count = sum(1 for w in wells if w["delta_temp_c"] >= baseline_val)
            after_count = sum(1 for w in wells if w["delta_temp_c"] >= simulated_val)
            net_change = after_count - before_count

            for w in wells:
                # Flipped from producing to stalled
                if baseline_val <= w["delta_temp_c"] < simulated_val:
                    insp_id = w["latest_inspection_id"]
                    if insp_id:
                        evidence_ids.append(insp_id)
                    flipped_assets.append({
                        "asset_id": w["asset_id"],
                        "record_id": insp_id,
                        "delta_temp_c": w["delta_temp_c"],
                        "before_status": "Producing (delta >= baseline)",
                        "simulated_status": "Stalled / Shut-In (delta < simulated)",
                        "evidence_ids": [insp_id] if insp_id else [],
                    })

            scenario_name = f"Temperature Stall Threshold ({target_type}): {baseline_val} deg C -> {simulated_val} deg C"
            param_changed = "threshold_temp_delta"
            y_axis_label = f"Active Producing Wells ({target_type})"

        # Check ledger count again to guarantee non-destructive execution
        cursor.execute("SELECT COUNT(*) FROM ledger")
        final_ledger_count = cursor.fetchone()[0]
        assert final_ledger_count == initial_ledger_count, "Invariant violated: simulator must never mutate ledger!"

        unique_evidence = sorted(list(set(evidence_ids)))

        # Generative UI Bar Chart Block
        visual_block = {
            "block_type": "bar_chart",
            "title": f"⚡ What-If Simulation: {scenario_name}",
            "labels": ["Baseline Policy", "Counterfactual State"],
            "series": [
                {
                    "name": y_axis_label,
                    "values": [before_count, after_count],
                }
            ],
            "unit": "assets/records",
            "delta": net_change,
        }

        # Generative UI Table Block for flipped assets
        table_rows = []
        for fa in flipped_assets[:10]:
            table_rows.append({
                "Asset ID": fa["asset_id"],
                "Record ID": str(fa.get("record_id", "")),
                "Baseline State": fa["before_status"],
                "Simulated State": fa["simulated_status"],
                "Evidence": " ".join([f"[{e}]" for e in fa.get("evidence_ids", [])]),
            })

        return {
            "scenario_name": scenario_name,
            "parameter_changed": param_changed,
            "baseline_value": baseline_val,
            "simulated_value": simulated_val,
            "before_count": before_count,
            "after_count": after_count,
            "net_change": net_change,
            "flipped_assets_count": len(flipped_assets),
            "flipped_assets_sample": flipped_assets[:15],
            "evidence_ids": unique_evidence,
            "visual": visual_block,
            "flipped_table": {
                "block_type": "table",
                "title": f"Flipped Assets Under Simulation ({len(flipped_assets)} Total)",
                "columns": ["Asset ID", "Record ID", "Baseline State", "Simulated State", "Evidence"],
                "rows": table_rows,
            },
        }

    finally:
        if close_conn:
            conn.close()
