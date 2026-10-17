import sqlite3
from typing import Any, Dict, List, Optional
from backend.copilot.db import get_connection


def calculate_well_downtime(
    well_id: str,
    start_date: str,
    end_date: str,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Calculate downtime for a well in a given date window.
    Domain rule: Every inspection in the period finding wellhead not producing oil
    counts as exactly 7 days of downtime.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.inspection_id, e.inspected_date, e.ambient_temp_c,
               e.effective_wellhead_temp_c, e.delta_temp_c, e.threshold_temp_delta,
               e.is_producing, e.inspector_notes
        FROM eff_inspection e
        WHERE e.asset_id = ?
          AND e.inspected_date >= ?
          AND e.inspected_date <= ?
        ORDER BY e.inspected_date ASC
    """, (well_id, start_date, end_date))

    rows = cursor.fetchall()

    down_inspections = []
    down_days = 0

    for r in rows:
        if r["is_producing"] == 0:
            down_days += 7

            # Look up any maintenance job active around or triggered by this inspection
            insp_id = r["inspection_id"]
            insp_date = r["inspected_date"]

            cursor.execute("""
                SELECT maintenance_id, issue, action_taken, started_at, completed_at
                FROM maintenance
                WHERE asset_id = ?
                  AND (
                    triggered_by_inspection_id = ?
                    OR (started_at <= ? AND (completed_at IS NULL OR completed_at >= ?))
                  )
                ORDER BY started_at ASC
            """, (well_id, insp_id, f"{insp_date}T23:59:59Z", f"{insp_date}T00:00:00Z"))
            rep = cursor.fetchone()

            down_inspections.append({
                "inspection_id": insp_id,
                "date": insp_date,
                "ambient_temp_c": r["ambient_temp_c"],
                "wellhead_temp_c": r["effective_wellhead_temp_c"],
                "delta_temp_c": r["delta_temp_c"],
                "threshold_temp_delta": r["threshold_temp_delta"],
                "inspector_notes": r["inspector_notes"],
                "cause_repair_id": rep["maintenance_id"] if rep else None,
                "cause_issue": rep["issue"] if rep else None,
                "cause_action": rep["action_taken"] if rep else None,
            })

    if close_conn:
        conn.close()

    return {
        "well_id": well_id,
        "start_date": start_date,
        "end_date": end_date,
        "downtime_days": down_days,
        "down_inspections_count": len(down_inspections),
        "total_inspections_in_window": len(rows),
        "inspections": down_inspections,
    }


def get_area_downtime_ranking(
    area_id: str,
    start_date: str,
    end_date: str,
    top_n: int = 3,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Rank wells in an area by total downtime days within the specified date window.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.asset_id, a.name, a.well_type,
               SUM(CASE WHEN e.is_producing = 0 THEN 7 ELSE 0 END) as downtime_days,
               SUM(CASE WHEN e.is_producing = 0 THEN 1 ELSE 0 END) as down_count
        FROM eff_inspection e
        JOIN assets a ON e.asset_id = a.asset_id
        WHERE e.area_id = ?
          AND e.inspected_date >= ?
          AND e.inspected_date <= ?
        GROUP BY e.asset_id, a.name, a.well_type
        ORDER BY downtime_days DESC, e.asset_id ASC
    """, (area_id, start_date, end_date))

    all_rows = [
        {
            "well_id": r["asset_id"],
            "name": r["name"],
            "well_type": r["well_type"],
            "downtime_days": r["downtime_days"],
            "down_inspections_count": r["down_count"],
        }
        for r in cursor.fetchall()
    ]

    top_wells = all_rows[:top_n]
    runner_up = all_rows[top_n] if len(all_rows) > top_n else None

    if close_conn:
        conn.close()

    return {
        "area_id": area_id,
        "start_date": start_date,
        "end_date": end_date,
        "top_wells": top_wells,
        "runner_up": runner_up,
        "all_rankings": all_rows,
    }
