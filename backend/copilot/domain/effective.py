import json
import re
import sqlite3
from typing import Any, Dict, List, Optional
from backend.copilot.config import AS_OF
from backend.copilot.ingest.rules import load_rules


def get_threshold_map() -> Dict[str, float]:
    """Return map of well_type -> production_temp_delta from rules.yaml."""
    rules_data = load_rules()
    t_map = {"T200": 15.0, "T350": 20.0}
    for r in rules_data.get("rules", []):
        if r.get("param") == "production_temp_delta":
            t_map[r["applies_to"]] = float(r["value"])
    return t_map


def materialize_derived_tables(conn: sqlite3.Connection) -> None:
    """
    Populate derived tables eff_inspection, well_now, and spills deterministically.
    """
    thresholds = get_threshold_map()

    with conn:
        # 1. Clean existing derived tables
        conn.execute("DELETE FROM eff_inspection")
        conn.execute("DELETE FROM well_now")
        conn.execute("DELETE FROM spills")

        # 2. Pre-load corrections from raw context_notes (rainwater false alarms from dataset)
        corrections: Dict[str, Dict[str, Any]] = {}
        cursor = conn.cursor()
        cursor.execute("""
            SELECT note_id, asset_id, inspection_id, text, author_user_id, note_type
            FROM context_notes
            WHERE note_type IN ('correction', 'volume_correction') AND inspection_id IS NOT NULL
            ORDER BY created_at ASC
        """)
        for row in cursor.fetchall():
            note_id, asset_id, insp_id, text, author = row[0], row[1], row[2], row[3], row[4]
            is_rainwater = any(w in text.lower() for w in ["rainwater", "water", "no crude", "not a crude", "not a spill"])
            # Temperature override check
            t_match = re.search(r"(?:re-measured|measured).*?(\d+(?:\.\d+)?)\s*°C", text, re.I)
            override_temp = float(t_match.group(1)) if t_match else None
            # Volume override check
            v_match = re.search(r"(?:measured|estimated).*?(\d+(?:\.\d+)?)\s*bbl", text, re.I)
            override_vol = float(v_match.group(1)) if v_match else None

            corrections[insp_id] = {
                "note_id": note_id,
                "text": text,
                "author": author,
                "is_spill_corrected": 1 if is_rainwater else 0,
                "override_temp": override_temp,
                "override_vol": override_vol,
            }

        # 2b. Overlay runtime corrections from append-only ledger (Rule 3: raw tables immutable)
        cursor.execute("""
            SELECT entry_id, user_id, scope_type, scope_id, entry_type, payload_json, reason
            FROM ledger
            WHERE entry_type IN ('raw_correction', 'analysis_correction')
            ORDER BY created_at ASC
        """)
        for l_row in cursor.fetchall():
            l_id, l_user, l_scope_type, l_scope_id, l_type, l_payload_str, l_reason = (
                l_row[0], l_row[1], l_row[2], l_row[3], l_row[4], l_row[5], l_row[6]
            )
            payload = json.loads(l_payload_str)
            insp_id = l_scope_id if l_scope_type == "inspection" else payload.get("inspection_id", l_scope_id)
            if not insp_id:
                continue

            curr = corrections.get(insp_id, {
                "note_id": l_id,
                "text": l_reason or "Ledger correction",
                "author": l_user,
                "is_spill_corrected": 0,
                "override_temp": None,
                "override_vol": None,
            })
            curr["note_id"] = l_id
            curr["author"] = l_user
            if l_reason:
                curr["text"] = l_reason

            if "corrected_wellhead_temp" in payload:
                curr["override_temp"] = float(payload["corrected_wellhead_temp"])
            if "corrected_volume_bbl" in payload:
                curr["override_vol"] = float(payload["corrected_volume_bbl"])

            corrections[insp_id] = curr

        # 3. Build eff_inspection
        cursor.execute("""
            SELECT i.inspection_id, i.asset_id, a.well_type, a.area_id, i.inspected_at,
                   i.inspected_date, i.inspector_user_id, i.method, i.ambient_temp_c,
                   i.wellhead_temp_c, i.spill_detected, i.spill_area_pct,
                   i.spill_est_volume_bbl, i.notes
            FROM inspections i
            JOIN assets a ON i.asset_id = a.asset_id
            ORDER BY i.inspected_at ASC
        """)
        inspections = cursor.fetchall()

        eff_rows = []
        for row in inspections:
            insp_id = row[0]
            asset_id = row[1]
            well_type = row[2]
            area_id = row[3]
            insp_at = row[4]
            insp_date = row[5]
            inspector_user = row[6]
            method = row[7]
            amb_temp = row[8]
            raw_wht = row[9]
            raw_spill = row[10]
            raw_area_pct = row[11]
            raw_vol = row[12]
            notes = row[13]

            corr = corrections.get(insp_id)
            eff_wht = corr["override_temp"] if (corr and corr["override_temp"] is not None) else raw_wht
            delta_temp = round(eff_wht - amb_temp, 2) if (eff_wht is not None and amb_temp is not None) else None
            thresh = thresholds.get(well_type, 15.0)

            is_producing = 1 if (delta_temp is not None and delta_temp >= thresh) else 0

            is_spill_corr = corr["is_spill_corrected"] if corr else 0
            eff_spill_det = 0 if is_spill_corr else raw_spill
            eff_vol = corr["override_vol"] if (corr and corr["override_vol"] is not None) else raw_vol

            eff_rows.append((
                insp_id, asset_id, well_type, area_id, insp_at, insp_date, inspector_user,
                method, amb_temp, raw_wht, eff_wht, delta_temp, thresh, is_producing,
                raw_spill, eff_spill_det, eff_vol, raw_area_pct, is_spill_corr,
                corr["note_id"] if corr else None, corr["text"] if corr else None, notes
            ))

        conn.executemany("""
            INSERT INTO eff_inspection (
                inspection_id, asset_id, well_type, area_id, inspected_at, inspected_date,
                inspector_user_id, method, ambient_temp_c, raw_wellhead_temp_c,
                effective_wellhead_temp_c, delta_temp_c, threshold_temp_delta, is_producing,
                raw_spill_detected, effective_spill_detected, effective_spill_volume_bbl,
                effective_spill_area_pct, is_spill_corrected, correction_note_id,
                correction_note_text, inspector_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, eff_rows)

        # 4. Build well_now (latest inspection per well)
        cursor.execute("""
            WITH latest AS (
                SELECT asset_id, MAX(inspected_at) as max_at
                FROM eff_inspection
                GROUP BY asset_id
            )
            SELECT e.asset_id, e.well_type, e.area_id, a.team_id, a.name, a.lat, a.lon,
                   e.inspection_id, e.inspected_at, e.inspected_date, e.inspector_user_id,
                   u.name as inspector_name, e.method, e.ambient_temp_c, e.effective_wellhead_temp_c,
                   e.delta_temp_c, e.threshold_temp_delta, e.is_producing, a.recorded_status,
                   e.inspector_notes
            FROM latest l
            JOIN eff_inspection e ON e.asset_id = l.asset_id AND e.inspected_at = l.max_at
            JOIN assets a ON e.asset_id = a.asset_id
            LEFT JOIN users u ON e.inspector_user_id = u.user_id
        """)
        latest_wells = cursor.fetchall()

        # Load open maintenance and active notes for reasoning
        cursor.execute("""
            SELECT maintenance_id, asset_id, issue, started_at, completed_at
            FROM maintenance
            WHERE completed_at IS NULL OR completed_at > ?
        """, (AS_OF,))
        open_repairs: Dict[str, List[sqlite3.Row]] = {}
        for r in cursor.fetchall():
            open_repairs.setdefault(r["asset_id"], []).append(r)

        cursor.execute("""
            SELECT note_id, asset_id, text, author_user_id, valid_from, valid_to, u.name as author_name
            FROM context_notes c
            LEFT JOIN users u ON c.author_user_id = u.user_id
            WHERE note_type != 'correction'
              AND (valid_from IS NULL OR valid_from <= ?)
              AND (valid_to IS NULL OR valid_to >= ?)
            ORDER BY c.valid_from DESC, c.created_at DESC
        """, (AS_OF, AS_OF))
        active_notes: Dict[str, List[sqlite3.Row]] = {}
        for n in cursor.fetchall():
            active_notes.setdefault(n["asset_id"], []).append(n)

        # Include runtime well_fact notes from ledger
        cursor.execute("""
            SELECT l.entry_id, l.scope_id as asset_id, l.payload_json,
                   l.user_id as author_user_id, l.created_at, u.name as author_name
            FROM ledger l
            LEFT JOIN users u ON l.user_id = u.user_id
            WHERE l.entry_type = 'well_fact' AND l.scope_type = 'well'
            ORDER BY l.created_at DESC
        """)
        for l_row in cursor.fetchall():
            payload = json.loads(l_row[2])
            vf = payload.get("valid_from")
            vt = payload.get("valid_to")
            if (vf is None or vf <= AS_OF) and (vt is None or vt >= AS_OF):
                note_dict = {
                    "note_id": l_row[0],
                    "asset_id": l_row[1],
                    "text": payload.get("text", ""),
                    "author_user_id": l_row[3],
                    "valid_from": vf,
                    "valid_to": vt,
                    "author_name": l_row[5],
                }
                active_notes.setdefault(l_row[1], []).append(note_dict)

        well_now_rows = []
        for w in latest_wells:
            asset_id = w["asset_id"]
            is_prod = w["is_producing"]
            rec_status = w["recorded_status"]

            # Staleness: active in DB but not producing, or down in DB but producing
            status_is_stale = 1 if ((rec_status == "active" and not is_prod) or (rec_status == "down" and is_prod)) else 0

            reason_type = "producing" if is_prod else "no_recorded_reason"
            reason_ref_id = None
            reason_summary = "Well is producing normally." if is_prod else "No recorded reason"

            if not is_prod:
                # Priority 1: open repair
                repairs = open_repairs.get(asset_id, [])
                if repairs:
                    rep = repairs[0]
                    reason_type = "repair"
                    reason_ref_id = rep["maintenance_id"]
                    start_date = rep["started_at"][:10]
                    reason_summary = f"Repair {rep['maintenance_id']}, {rep['issue']}, started {start_date}, still open"
                else:
                    # Priority 2: active human context note
                    notes_list = active_notes.get(asset_id, [])
                    if notes_list:
                        n = notes_list[0]
                        reason_type = "context_note"
                        reason_ref_id = n["note_id"]
                        reason_summary = f"Note {n['note_id']} by {n['author_name'] or n['author_user_id']}: {n['text']}"
                    else:
                        reason_type = "no_recorded_reason"
                        insp_remark = w["inspector_notes"]
                        if insp_remark:
                            reason_summary = f"No recorded reason. The inspector noted \"{insp_remark}\""
                        else:
                            reason_summary = "No recorded reason"

            well_now_rows.append((
                asset_id, w["well_type"], w["area_id"], w["team_id"], w["name"],
                w["lat"], w["lon"], w["inspection_id"], w["inspected_at"],
                w["inspected_date"], w["inspector_user_id"], w["inspector_name"],
                w["method"], w["ambient_temp_c"], w["effective_wellhead_temp_c"],
                w["delta_temp_c"], w["threshold_temp_delta"], is_prod, rec_status,
                status_is_stale, reason_type, reason_ref_id, reason_summary, w["inspector_notes"]
            ))

        conn.executemany("""
            INSERT INTO well_now (
                asset_id, well_type, area_id, team_id, name, lat, lon, latest_inspection_id,
                latest_inspected_at, latest_inspected_date, inspector_user_id, inspector_name,
                method, ambient_temp_c, wellhead_temp_c, delta_temp_c, threshold_temp_delta,
                is_producing, recorded_status, status_is_stale, reason_type, reason_ref_id,
                reason_summary, inspector_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, well_now_rows)

        # 5. Build spills table (non-corrected spills with location and containment info)
        cursor.execute("""
            SELECT e.inspection_id, e.asset_id, e.well_type, e.area_id, ar.name as area_name,
                   a.team_id, e.inspected_date, e.inspected_at, e.effective_spill_volume_bbl,
                   e.effective_spill_area_pct, a.lat, a.lon,
                   m.maintenance_id, rf.contained_hours, rf.report_file, i.evidence_images_json
            FROM eff_inspection e
            JOIN assets a ON e.asset_id = a.asset_id
            JOIN areas ar ON e.area_id = ar.area_id
            JOIN inspections i ON e.inspection_id = i.inspection_id
            LEFT JOIN maintenance m ON e.inspection_id = m.triggered_by_inspection_id
            LEFT JOIN report_facts rf ON m.maintenance_id = rf.maintenance_id
            WHERE e.effective_spill_detected = 1
              AND e.effective_spill_volume_bbl IS NOT NULL
            ORDER BY e.inspected_at ASC
        """)
        spill_rows = []
        for r in cursor.fetchall():
            vol = r[8]
            is_rep = 1 if (vol is not None and vol >= 5.0) else 0
            is_maj = 1 if (vol is not None and vol >= 25.0) else 0
            spill_id = f"SPILL-{r[0]}"
            spill_rows.append((
                spill_id, r[1], r[0], r[2], r[3], r[4], r[5], r[6], vol,
                r[9], r[10], r[11], is_rep, is_maj, r[12], r[13], r[14], r[15]
            ))

        conn.executemany("""
            INSERT INTO spills (
                spill_id, asset_id, inspection_id, well_type, area_id, area_name, team_id,
                date, volume_bbl, pad_area_pct, lat, lon, is_reportable, is_major,
                triggered_maintenance_id, contained_hours, report_file, evidence_images_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, spill_rows)

        conn.commit()
