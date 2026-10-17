import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional
from dateutil.relativedelta import relativedelta

from backend.copilot.config import AS_OF
from backend.copilot.db import get_connection
from backend.copilot.domain.params import ParameterResolver


def evaluate_well_compliance(
    well_id: str,
    start_date: str,
    end_date: str,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Deterministically evaluate compliance protocols for a well over a date window.
    Evaluates:
      - SR-01 (Spill reporting deadlines & Notices of Violation)
      - SR-02 (4-hour containment limit from repair reports)
      - SR-03 (60-day cleanup verification requirement)
      - RC-02 (Annual flowline integrity test per calendar year)
      - RC-04 (30-day response to Notice of Violation)
      - Manual §10 RCA requirement on recurring equipment repairs
      - Manual §4 Planned shut-in maintenance recording rule
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    params = ParameterResolver(conn)

    breaches = []
    pending_actions = []
    rules_met = []
    total_open_fines = 0.0

    # 1. Evaluate Spills & SR-01, SR-02, SR-03
    cursor.execute("""
        SELECT s.spill_id, s.inspection_id, s.date, s.volume_bbl, s.is_reportable,
               s.is_major, s.triggered_maintenance_id, s.contained_hours, s.report_file
        FROM spills s
        WHERE s.asset_id = ?
          AND s.date >= ?
          AND s.date <= ?
        ORDER BY s.date ASC
    """, (well_id, start_date, end_date))
    well_spills = cursor.fetchall()

    for sp in well_spills:
        insp_id = sp["inspection_id"]
        sp_date = sp["date"]
        vol = sp["volume_bbl"]
        is_rep = sp["is_reportable"]
        cont_hrs = sp["contained_hours"]
        mnt_id = sp["triggered_maintenance_id"]

        # SR-02: Containment deadline (4.0 hours)
        sr02_limit = params.get_param("sr02_containment_deadline_hours", well_id=well_id, default=4.0)["value"]
        if cont_hrs and cont_hrs > sr02_limit:
            breaches.append({
                "protocol_id": "SR-02",
                "description": f"Release contained after about {cont_hrs} hours against {sr02_limit}-hour limit",
                "report_id": mnt_id,
                "inspection_id": insp_id,
                "date": sp_date,
                "contained_hours": cont_hrs,
            })

        # If reportable or major, check SR-01 and SR-03
        if is_rep:
            # Query regulatory events for this inspection
            cursor.execute("""
                SELECT event_id, event_date, event_type, protocol_id, hours_to_report, detail, fine_usd, status
                FROM regulatory_events
                WHERE asset_id = ? AND related_inspection_id = ?
            """, (well_id, insp_id))
            reg_events = cursor.fetchall()

            # SR-01 check
            sr01_limit = params.get_param("sr01_written_report_deadline_hours", well_id=well_id, default=24.0)["value"]
            spill_reported_evt = next((e for e in reg_events if e["event_type"] == "spill_report_filed"), None)
            nov_evt = next((e for e in reg_events if e["event_type"] == "notice_of_violation"), None)

            if spill_reported_evt and spill_reported_evt["hours_to_report"] and spill_reported_evt["hours_to_report"] > sr01_limit:
                fine = nov_evt["fine_usd"] if nov_evt else 0.0
                fine_status = nov_evt["status"] if nov_evt else "none"
                if fine_status == "open":
                    total_open_fines += fine

                breaches.append({
                    "protocol_id": "SR-01",
                    "description": f"Spill report filed after {spill_reported_evt['hours_to_report']} hours against {sr01_limit}-hour limit",
                    "event_id": spill_reported_evt["event_id"],
                    "nov_event_id": nov_evt["event_id"] if nov_evt else None,
                    "fine_usd": fine,
                    "fine_status": fine_status,
                    "inspection_id": insp_id,
                    "date": sp_date,
                })
            elif not spill_reported_evt:
                # No report filed for reportable spill!
                breaches.append({
                    "protocol_id": "SR-01",
                    "description": f"Reportable spill ({vol} bbl) has no written notice on record within {sr01_limit} hours",
                    "inspection_id": insp_id,
                    "date": sp_date,
                    "fine_usd": 0,
                    "fine_status": "open",
                })

            # RC-04: Notice of violation response due in 30 days
            if nov_evt:
                nov_date = datetime.date.fromisoformat(nov_evt["event_date"])
                rc04_deadline = nov_date + datetime.timedelta(days=30)
                # Check for nov_response_filed
                cursor.execute("""
                    SELECT event_id FROM regulatory_events
                    WHERE asset_id = ? AND event_type = 'nov_response_filed' AND related_inspection_id = ?
                """, (well_id, insp_id))
                resp_evt = cursor.fetchone()
                if not resp_evt and rc04_deadline.isoformat() <= AS_OF:
                    breaches.append({
                        "protocol_id": "RC-04",
                        "description": f"Notice of violation response due by {rc04_deadline.isoformat()} (30 days from {nov_date}), no response recorded",
                        "nov_event_id": nov_evt["event_id"],
                        "due_date": rc04_deadline.isoformat(),
                    })

            # SR-03: Cleanup verification due within 60 days
            sr03_site_insp = next((e for e in reg_events if e["protocol_id"] == "SR-03"), None)
            sp_date_dt = datetime.date.fromisoformat(sp_date)
            sr03_due = sp_date_dt + datetime.timedelta(days=60)
            if sr03_site_insp and sr03_site_insp["status"] == "open" and sr03_due.isoformat() <= AS_OF:
                breaches.append({
                    "protocol_id": "SR-03",
                    "description": f"Cleanup verification due by {sr03_due.isoformat()} (60 days) and still open",
                    "event_id": sr03_site_insp["event_id"],
                    "status": "open",
                    "due_date": sr03_due.isoformat(),
                })

    # 2. RC-02: Annual Flowline Integrity Test
    # Checks if flowline test was performed in the calendar year of end_date
    cal_year = end_date[:4]
    cursor.execute("""
        SELECT maintenance_id, started_at, issue
        FROM maintenance
        WHERE asset_id = ?
          AND started_at >= ?
          AND started_at <= ?
          AND issue LIKE '%flowline integrity test%'
    """, (well_id, f"{cal_year}-01-01", f"{cal_year}-12-31"))
    fl_test = cursor.fetchone()
    if fl_test:
        rules_met.append({
            "protocol_id": "RC-02",
            "description": f"Annual flowline integrity test passed on {fl_test['started_at'][:10]}",
            "maintenance_id": fl_test["maintenance_id"],
        })
    else:
        breaches.append({
            "protocol_id": "RC-02",
            "description": f"No annual flowline integrity test recorded for calendar year {cal_year}",
        })

    # 3. Maintenance Escalation: RCA Trigger (3+ corrective events on same equipment in 12 months)
    rca_thresh = params.get_param("rca_corrective_count", well_id=well_id, default=3)["value"]
    cursor.execute("""
        SELECT equipment_kind, COUNT(*) as cnt, GROUP_CONCAT(maintenance_id, ', ') as mnt_ids
        FROM maintenance
        WHERE asset_id = ?
          AND maintenance_type = 'corrective'
          AND started_at >= ?
          AND started_at <= ?
        GROUP BY equipment_kind
        HAVING cnt >= ?
    """, (well_id, start_date, f"{end_date}T23:59:59Z", rca_thresh))
    rca_rows = cursor.fetchall()
    for row in rca_rows:
        equip = row["equipment_kind"]
        cnt = row["cnt"]
        m_ids = row["mnt_ids"].split(", ")
        pending_actions.append({
            "item": f"{equip}_rca",
            "description": f"Root-cause analysis due on {equip}: {cnt} corrective repairs in the last 12 months ({', '.join(m_ids)})",
            "status": "Action required",
            "equipment": equip,
            "repairs": m_ids,
        })

    # 4. Start-up and shut-in rule (planned shut-in recorded in maintenance system before work)
    cursor.execute("""
        SELECT note_id, text, author_user_id, valid_from, valid_to
        FROM context_notes
        WHERE asset_id = ?
          AND text LIKE '%shut in%'
          AND text LIKE '%not yet in the maintenance system%'
          AND (valid_to IS NULL OR valid_to >= ?)
    """, (well_id, AS_OF))
    unrec_shutin = cursor.fetchone()
    if unrec_shutin:
        pending_actions.append({
            "item": "planned_shutin_unrecorded",
            "description": "Planned shut-in is not yet recorded in the maintenance system, which manual requires before work starts",
            "note_id": unrec_shutin["note_id"],
            "status": "Action required",
        })

    if close_conn:
        conn.close()

    return {
        "well_id": well_id,
        "window": {"start_date": start_date, "end_date": end_date},
        "breaches_count": len(breaches),
        "breaches": breaches,
        "total_open_fines_usd": total_open_fines,
        "pending_actions": pending_actions,
        "rules_met": rules_met,
    }


def get_uncontained_spills(
    area_id: str,
    start_date: str,
    end_date: str,
    limit_hours: float = 4.0,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Retrieve spills in an area during a date window that exceeded the containment time limit.
    Containment hours are sourced directly from parsed repair reports.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.spill_id, s.asset_id, s.inspection_id, s.date, s.volume_bbl,
               s.triggered_maintenance_id, s.contained_hours, s.report_file
        FROM spills s
        WHERE s.area_id = ?
          AND s.date >= ?
          AND s.date <= ?
          AND s.contained_hours > ?
        ORDER BY s.contained_hours DESC, s.date DESC
    """, (area_id, start_date, end_date, limit_hours))

    items = [
        {
            "spill_id": r["spill_id"],
            "well_id": r["asset_id"],
            "inspection_id": r["inspection_id"],
            "date": r["date"],
            "volume_bbl": r["volume_bbl"],
            "report_id": r["triggered_maintenance_id"],
            "contained_hours": r["contained_hours"],
            "report_file": r["report_file"],
        }
        for r in cursor.fetchall()
    ]

    if close_conn:
        conn.close()

    return {
        "area_id": area_id,
        "start_date": start_date,
        "end_date": end_date,
        "limit_hours": limit_hours,
        "count": len(items),
        "items": items,
    }
