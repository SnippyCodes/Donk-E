import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import sqlite3

from backend.copilot.config import (
    DATABASE_PATH,
    ensure_data_dirs,
    get_dataset_roots,
)
from backend.copilot.db import get_connection, init_db
from backend.copilot.ingest.reports import ReportParser
from backend.copilot.ingest.docs import init_doc_fts, extract_all_doc_chunks, index_doc_chunks
from backend.copilot.ingest.rules import generate_rules_yaml


def load_dataset(db_path: Optional[str] = None, roots: Optional[List[Path]] = None) -> Dict[str, int]:
    """
    Ingest multi-root dataset into SQLite database idempotently and efficiently.
    Returns counts of ingested records.
    """
    start_time = time.time()
    ensure_data_dirs()
    conn = get_connection(db_path)
    init_db(conn)
    init_doc_fts(conn)

    dataset_roots = roots or get_dataset_roots()
    if not dataset_roots:
        raise FileNotFoundError("No valid dataset roots found in configuration.")

    counts = {
        "areas": 0,
        "teams": 0,
        "users": 0,
        "assets": 0,
        "equipment": 0,
        "inspections": 0,
        "maintenance": 0,
        "regulatory_events": 0,
        "context_notes": 0,
        "report_facts": 0,
        "doc_chunks": 0,
    }

    # Extract & write rules.yaml if not present
    generate_rules_yaml()

    # Index documentation chunks
    chunks = extract_all_doc_chunks()
    counts["doc_chunks"] = index_doc_chunks(conn, chunks)

    # Process dataset roots
    for root in dataset_roots:
        fleet_dir = root / "fleet"
        assets_dir = root / "assets"

        # 1. Ingest Fleet Areas & Teams
        areas_file = fleet_dir / "areas.json"
        if areas_file.exists():
            with open(areas_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            areas_rows = []
            for a in data.get("areas", []):
                areas_rows.append((
                    a["area_id"],
                    a["name"],
                    a["team_id"],
                    a.get("center", {}).get("lat"),
                    a.get("center", {}).get("lon"),
                    json.dumps(a.get("asset_ids", []))
                ))
            conn.executemany("""
                INSERT OR REPLACE INTO areas (area_id, name, team_id, center_lat, center_lon, asset_ids_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, areas_rows)
            counts["areas"] += len(areas_rows)

            teams_rows = []
            for t in data.get("teams", []):
                teams_rows.append((
                    t["team_id"],
                    t["name"],
                    t.get("lead_user_id")
                ))
            conn.executemany("""
                INSERT OR REPLACE INTO teams (team_id, name, lead_user_id)
                VALUES (?, ?, ?)
            """, teams_rows)
            counts["teams"] += len(teams_rows)

        # 2. Ingest Users
        users_file = fleet_dir / "users.json"
        if users_file.exists():
            with open(users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            users_rows = []
            for u in data.get("users", []):
                users_rows.append((
                    u["user_id"],
                    u["name"],
                    u["role"],
                    u.get("team_id")
                ))
            conn.executemany("""
                INSERT OR REPLACE INTO users (user_id, name, role, team_id)
                VALUES (?, ?, ?, ?)
            """, users_rows)
            counts["users"] += len(users_rows)

        # 3. Ingest Assets and their records
        if assets_dir.exists():
            asset_subdirs = sorted([p for p in assets_dir.iterdir() if p.is_dir()])

            assets_rows = []
            equip_rows = []
            insp_rows = []
            mnt_rows = []
            reg_rows = []
            ctx_rows = []
            report_rows = []

            for well_dir in asset_subdirs:
                asset_id = well_dir.name

                # metadata.json
                meta_file = well_dir / "metadata.json"
                if meta_file.exists():
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    loc = meta.get("location", {})
                    last_insp = meta.get("last_inspection", {})
                    assets_rows.append((
                        meta["asset_id"],
                        meta.get("name", meta["asset_id"]),
                        meta.get("asset_category", "oil_well"),
                        meta.get("well_type", "T200"),
                        meta.get("area_id", ""),
                        meta.get("team_id", ""),
                        meta.get("in_charge_user_id"),
                        loc.get("lat"),
                        loc.get("lon"),
                        meta.get("installed_on"),
                        last_insp.get("inspection_id"),
                        last_insp.get("inspected_at"),
                        last_insp.get("inspector_user_id"),
                        meta.get("recorded_status", "active")
                    ))
                    for eq in meta.get("equipment", []):
                        equip_rows.append((
                            eq["equipment_id"],
                            meta["asset_id"],
                            eq.get("kind", ""),
                            eq.get("model", "")
                        ))

                # inspections.jsonl
                insp_file = well_dir / "inspections.jsonl"
                if insp_file.exists():
                    with open(insp_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            rec = json.loads(line)
                            insp_at = rec["inspected_at"]
                            insp_rows.append((
                                rec["inspection_id"],
                                rec["asset_id"],
                                insp_at,
                                insp_at[:10],
                                rec.get("inspector_user_id", ""),
                                rec.get("method", "drone"),
                                rec.get("ambient_temp_c"),
                                rec.get("wellhead_temp_c"),
                                1 if rec.get("spill_detected") else 0,
                                rec.get("spill_area_pct"),
                                rec.get("spill_est_volume_bbl"),
                                json.dumps(rec.get("evidence_images", [])),
                                rec.get("notes")
                            ))

                # maintenance.jsonl
                mnt_file = well_dir / "maintenance.jsonl"
                if mnt_file.exists():
                    with open(mnt_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            rec = json.loads(line)
                            costs = rec.get("cost_usd", {}) or {}
                            mnt_rows.append((
                                rec["maintenance_id"],
                                rec["asset_id"],
                                rec["started_at"],
                                rec.get("completed_at"),
                                rec.get("maintenance_type", "corrective"),
                                rec.get("equipment_kind", ""),
                                rec.get("issue", ""),
                                rec.get("action_taken", ""),
                                rec.get("technician_user_id"),
                                rec.get("contractor"),
                                rec.get("downtime_hours"),
                                costs.get("labor"),
                                costs.get("parts"),
                                costs.get("total"),
                                rec.get("triggered_by_inspection_id"),
                                rec.get("report_file")
                            ))

                # regulatory-events.jsonl
                reg_file = well_dir / "regulatory-events.jsonl"
                if reg_file.exists():
                    with open(reg_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            rec = json.loads(line)
                            reg_rows.append((
                                rec["event_id"],
                                rec["asset_id"],
                                rec.get("date", ""),
                                rec.get("agency", ""),
                                rec.get("event_type", ""),
                                rec.get("protocol_id"),
                                rec.get("related_inspection_id"),
                                rec.get("hours_to_report"),
                                rec.get("detail"),
                                rec.get("fine_usd", 0.0),
                                rec.get("status", "open")
                            ))

                # context.jsonl
                ctx_file = well_dir / "context.jsonl"
                if ctx_file.exists():
                    with open(ctx_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            rec = json.loads(line)
                            ctx_rows.append((
                                rec["note_id"],
                                rec["asset_id"],
                                rec.get("created_at", ""),
                                rec.get("author_user_id", ""),
                                rec.get("note_type", "operator_note"),
                                rec.get("inspection_id"),
                                rec.get("text", ""),
                                rec.get("valid_from"),
                                rec.get("valid_to")
                            ))

                # maintenance-reports/*.md
                reports_dir = well_dir / "maintenance-reports"
                if reports_dir.exists():
                    for rpt_path in reports_dir.glob("*.md"):
                        parsed = ReportParser.parse_report_file(rpt_path)
                        # Relative path inside well or dataset
                        rel_rpt = str(rpt_path.relative_to(root)).replace("\\", "/")
                        report_rows.append((
                            parsed["maintenance_id"],
                            parsed["asset_id"] or asset_id,
                            rel_rpt,
                            parsed["equipment"],
                            parsed["work_started"],
                            parsed["work_finished"],
                            parsed["well_stopped_hours"],
                            parsed["crew_lead_name"],
                            parsed["crew_lead_user_id"],
                            parsed["contractor"],
                            parsed["triggered_by_inspection_id"],
                            parsed["report_written"],
                            parsed["contained_hours"],
                            parsed["spill_volume_bbl"],
                            parsed["spill_area_pct"],
                            parsed["pressure_test_psi"],
                            parsed["pressure_test_mop_psi"],
                            parsed["pressure_test_hours"],
                            parsed["h2s_ppm"],
                            parsed["waste_volume_m3"],
                            parsed["waste_manifest_id"],
                            parsed["soil_samples"],
                            parsed["soil_tph_pct"],
                            parsed["compliance_json"],
                            parsed["raw_text"]
                        ))

            # Batch execute insertions
            conn.executemany("""
                INSERT OR REPLACE INTO assets (
                    asset_id, name, asset_category, well_type, area_id, team_id,
                    in_charge_user_id, lat, lon, installed_on, last_inspection_id,
                    last_inspected_at, last_inspector_user_id, recorded_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, assets_rows)
            counts["assets"] += len(assets_rows)

            conn.executemany("""
                INSERT OR REPLACE INTO equipment (equipment_id, asset_id, kind, model)
                VALUES (?, ?, ?, ?)
            """, equip_rows)
            counts["equipment"] += len(equip_rows)

            conn.executemany("""
                INSERT OR REPLACE INTO inspections (
                    inspection_id, asset_id, inspected_at, inspected_date, inspector_user_id,
                    method, ambient_temp_c, wellhead_temp_c, spill_detected, spill_area_pct,
                    spill_est_volume_bbl, evidence_images_json, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, insp_rows)
            counts["inspections"] += len(insp_rows)

            conn.executemany("""
                INSERT OR REPLACE INTO maintenance (
                    maintenance_id, asset_id, started_at, completed_at, maintenance_type,
                    equipment_kind, issue, action_taken, technician_user_id, contractor,
                    downtime_hours, cost_labor, cost_parts, cost_total, triggered_by_inspection_id, report_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, mnt_rows)
            counts["maintenance"] += len(mnt_rows)

            conn.executemany("""
                INSERT OR REPLACE INTO regulatory_events (
                    event_id, asset_id, event_date, agency, event_type, protocol_id,
                    related_inspection_id, hours_to_report, detail, fine_usd, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, reg_rows)
            counts["regulatory_events"] += len(reg_rows)

            conn.executemany("""
                INSERT OR REPLACE INTO context_notes (
                    note_id, asset_id, created_at, author_user_id, note_type,
                    inspection_id, text, valid_from, valid_to
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ctx_rows)
            counts["context_notes"] += len(ctx_rows)

            conn.executemany("""
                INSERT OR REPLACE INTO report_facts (
                    maintenance_id, asset_id, report_file, equipment, work_started,
                    work_finished, well_stopped_hours, crew_lead_name, crew_lead_user_id,
                    contractor, triggered_by_inspection_id, report_written, contained_hours,
                    spill_volume_bbl, spill_area_pct, pressure_test_psi, pressure_test_mop_psi,
                    pressure_test_hours, h2s_ppm, waste_volume_m3, waste_manifest_id,
                    soil_samples, soil_tph_pct, compliance_json, raw_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, report_rows)
            counts["report_facts"] += len(report_rows)

    conn.commit()

    # Materialize derived tables
    from backend.copilot.domain.effective import materialize_derived_tables
    materialize_derived_tables(conn)

    duration = time.time() - start_time
    print(f"Ingestion completed in {duration:.2f}s. Loaded counts: {counts}")
    conn.close()
    return counts


if __name__ == "__main__":
    load_dataset()
