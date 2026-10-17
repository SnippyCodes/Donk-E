import os
import sqlite3
from pathlib import Path
from typing import Optional
from backend.copilot.config import DATABASE_PATH, ensure_data_dirs


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a configured SQLite connection with row factories and WAL mode."""
    target = db_path or DATABASE_PATH
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all raw, derived, and ledger tables with necessary indices."""
    with conn:
        # 1. Raw Fleet and Asset Tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS areas (
                area_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                team_id TEXT NOT NULL,
                center_lat REAL,
                center_lon REAL,
                asset_ids_json TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                lead_user_id TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                team_id TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                asset_category TEXT NOT NULL,
                well_type TEXT NOT NULL,
                area_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                in_charge_user_id TEXT,
                lat REAL,
                lon REAL,
                installed_on TEXT,
                last_inspection_id TEXT,
                last_inspected_at TEXT,
                last_inspector_user_id TEXT,
                recorded_status TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                equipment_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                model TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)

        # 2. Raw Time-Series & Event Tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                inspection_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                inspected_at TEXT NOT NULL,
                inspected_date TEXT NOT NULL,
                inspector_user_id TEXT NOT NULL,
                method TEXT NOT NULL,
                ambient_temp_c REAL,
                wellhead_temp_c REAL,
                spill_detected INTEGER NOT NULL,
                spill_area_pct REAL,
                spill_est_volume_bbl REAL,
                evidence_images_json TEXT,
                notes TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS maintenance (
                maintenance_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                maintenance_type TEXT NOT NULL,
                equipment_kind TEXT NOT NULL,
                issue TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                technician_user_id TEXT,
                contractor TEXT,
                downtime_hours REAL,
                cost_labor REAL,
                cost_parts REAL,
                cost_total REAL,
                triggered_by_inspection_id TEXT,
                report_file TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS regulatory_events (
                event_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                event_date TEXT NOT NULL,
                agency TEXT NOT NULL,
                event_type TEXT NOT NULL,
                protocol_id TEXT,
                related_inspection_id TEXT,
                hours_to_report REAL,
                detail TEXT,
                fine_usd REAL DEFAULT 0,
                status TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS context_notes (
                note_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                author_user_id TEXT NOT NULL,
                note_type TEXT NOT NULL,
                inspection_id TEXT,
                text TEXT NOT NULL,
                valid_from TEXT,
                valid_to TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_facts (
                maintenance_id TEXT PRIMARY KEY,
                asset_id TEXT,
                report_file TEXT,
                equipment TEXT,
                work_started TEXT,
                work_finished TEXT,
                well_stopped_hours REAL,
                crew_lead_name TEXT,
                crew_lead_user_id TEXT,
                contractor TEXT,
                triggered_by_inspection_id TEXT,
                report_written TEXT,
                contained_hours REAL,
                spill_volume_bbl REAL,
                spill_area_pct REAL,
                pressure_test_psi INTEGER,
                pressure_test_mop_psi INTEGER,
                pressure_test_hours REAL,
                h2s_ppm REAL,
                waste_volume_m3 REAL,
                waste_manifest_id TEXT,
                soil_samples INTEGER,
                soil_tph_pct REAL,
                compliance_json TEXT,
                raw_text TEXT
            )
        """)

        # 3. Indices for High-Performance Querying
        conn.execute("CREATE INDEX IF NOT EXISTS idx_insp_asset_date ON inspections(asset_id, inspected_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_insp_asset_at ON inspections(asset_id, inspected_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_insp_spill ON inspections(spill_detected, inspected_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mnt_asset_date ON maintenance(asset_id, started_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mnt_trigger ON maintenance(triggered_by_inspection_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_asset ON regulatory_events(asset_id, event_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ctx_asset ON context_notes(asset_id, note_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rpt_trigger ON report_facts(triggered_by_inspection_id)")

        # 4. Derived Analytics Tables (Materialized in effective.py)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS eff_inspection (
                inspection_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                well_type TEXT NOT NULL,
                area_id TEXT NOT NULL,
                inspected_at TEXT NOT NULL,
                inspected_date TEXT NOT NULL,
                inspector_user_id TEXT NOT NULL,
                method TEXT NOT NULL,
                ambient_temp_c REAL,
                raw_wellhead_temp_c REAL,
                effective_wellhead_temp_c REAL,
                delta_temp_c REAL,
                threshold_temp_delta REAL,
                is_producing INTEGER NOT NULL,
                raw_spill_detected INTEGER NOT NULL,
                effective_spill_detected INTEGER NOT NULL,
                effective_spill_volume_bbl REAL,
                effective_spill_area_pct REAL,
                is_spill_corrected INTEGER NOT NULL,
                correction_note_id TEXT,
                correction_note_text TEXT,
                inspector_notes TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS well_now (
                asset_id TEXT PRIMARY KEY,
                well_type TEXT NOT NULL,
                area_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                name TEXT NOT NULL,
                lat REAL,
                lon REAL,
                latest_inspection_id TEXT NOT NULL,
                latest_inspected_at TEXT NOT NULL,
                latest_inspected_date TEXT NOT NULL,
                inspector_user_id TEXT NOT NULL,
                inspector_name TEXT,
                method TEXT NOT NULL,
                ambient_temp_c REAL,
                wellhead_temp_c REAL,
                delta_temp_c REAL,
                threshold_temp_delta REAL,
                is_producing INTEGER NOT NULL,
                recorded_status TEXT NOT NULL,
                status_is_stale INTEGER NOT NULL,
                reason_type TEXT NOT NULL,
                reason_ref_id TEXT,
                reason_summary TEXT,
                inspector_note TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS spills (
                spill_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                inspection_id TEXT NOT NULL,
                well_type TEXT NOT NULL,
                area_id TEXT NOT NULL,
                area_name TEXT NOT NULL,
                team_id TEXT NOT NULL,
                date TEXT NOT NULL,
                volume_bbl REAL NOT NULL,
                pad_area_pct REAL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                is_reportable INTEGER NOT NULL,
                is_major INTEGER NOT NULL,
                triggered_maintenance_id TEXT,
                contained_hours REAL,
                report_file TEXT,
                evidence_images_json TEXT
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_eff_asset_date ON eff_inspection(asset_id, inspected_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_eff_asset_at ON eff_inspection(asset_id, inspected_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_eff_area_prod ON eff_inspection(area_id, is_producing, inspected_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spills_date ON spills(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spills_area_date ON spills(area_id, date)")

        # 5. Append-Only Memory & Ledger Tables (M4 Spec)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                entry_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                user_id TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                entry_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                reason TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS runtime_corrections (
                correction_id TEXT PRIMARY KEY,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                original_value REAL,
                corrected_value REAL,
                author_user_id TEXT NOT NULL,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_corr_target ON runtime_corrections(target_id, field_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_corr_asset ON runtime_corrections(asset_id)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS well_type_rule_overrides (
                override_id TEXT PRIMARY KEY,
                well_type TEXT NOT NULL,
                rule_field TEXT NOT NULL,
                equipment_kind TEXT,
                original_value REAL,
                new_value REAL NOT NULL,
                author_user_id TEXT NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_override_type ON well_type_rule_overrides(well_type, rule_field)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS shared_asset_notes (
                note_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                author_user_id TEXT NOT NULL,
                note_text TEXT NOT NULL,
                valid_from TEXT,
                valid_to TEXT,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shared_notes_asset ON shared_asset_notes(asset_id, created_at)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id, session_date)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_messages (
                turn_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                query_text TEXT NOT NULL,
                response_summary TEXT,
                last_discussed_wells_json TEXT,
                session_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON user_messages(user_id, created_at)")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_recall (
                entry_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                query_text TEXT NOT NULL,
                response_summary TEXT,
                referenced_entities_json TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recall_user ON user_recall(user_id, timestamp)")

