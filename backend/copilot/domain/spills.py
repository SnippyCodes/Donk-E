import sqlite3
from typing import Any, Dict, List, Optional
from backend.copilot.db import get_connection


def get_well_spills(
    well_id: str,
    start_date: str,
    end_date: str,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Retrieve spills and detections for a specific well in a date window.
    Accounts for false positives and human context corrections.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()

    # Query all detections in window from eff_inspection
    cursor.execute("""
        SELECT e.inspection_id, e.inspected_date, e.raw_spill_detected,
               e.effective_spill_detected, e.effective_spill_volume_bbl,
               e.effective_spill_area_pct, e.is_spill_corrected,
               e.correction_note_id, e.correction_note_text
        FROM eff_inspection e
        WHERE e.asset_id = ?
          AND e.inspected_date >= ?
          AND e.inspected_date <= ?
          AND (e.raw_spill_detected = 1 OR e.effective_spill_detected = 1)
        ORDER BY e.inspected_date ASC
    """, (well_id, start_date, end_date))

    rows = cursor.fetchall()

    total_detections = len(rows)
    real_spills = []
    corrections = []
    total_vol = 0.0

    for r in rows:
        if r["is_spill_corrected"] == 1:
            corrections.append({
                "inspection_id": r["inspection_id"],
                "date": r["inspected_date"],
                "note_id": r["correction_note_id"],
                "text": r["correction_note_text"],
            })
        else:
            vol = r["effective_spill_volume_bbl"] or 0.0
            total_vol += vol
            real_spills.append({
                "date": r["inspected_date"],
                "inspection_id": r["inspection_id"],
                "volume_bbl": round(vol, 1),
                "pad_area_pct": r["effective_spill_area_pct"],
            })

    if close_conn:
        conn.close()

    return {
        "well_id": well_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_detections": total_detections,
        "corrected_detections": len(corrections),
        "real_spills_count": len(real_spills),
        "total_volume_bbl": round(total_vol, 1),
        "spills": real_spills,
        "corrections": corrections,
    }


def get_area_spills_map(
    area_id: str,
    start_date: str,
    end_date: str,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Get map pins for all real spills in an area during the specified window.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT spill_id, asset_id, inspection_id, date, volume_bbl,
               pad_area_pct, lat, lon
        FROM spills
        WHERE area_id = ?
          AND date >= ?
          AND date <= ?
        ORDER BY date DESC, asset_id ASC
    """, (area_id, start_date, end_date))

    pins = [
        {
            "spill_id": r["spill_id"],
            "well_id": r["asset_id"],
            "inspection_id": r["inspection_id"],
            "date": r["date"],
            "volume_bbl": r["volume_bbl"],
            "pad_area_pct": r["pad_area_pct"],
            "lat": r["lat"],
            "lon": r["lon"],
        }
        for r in cursor.fetchall()
    ]

    if close_conn:
        conn.close()

    return {
        "area_id": area_id,
        "start_date": start_date,
        "end_date": end_date,
        "count": len(pins),
        "pins": pins,
    }


def get_spills_heatmap(
    year: str = "2026",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Aggregate real spills by geographic area and month for a calendar year.
    Returns a matrix suitable for heatmap visualization.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
        SELECT ar.name as area_name,
               CAST(strftime('%m', s.date) AS INTEGER) as month_num,
               COUNT(*) as spill_count
        FROM spills s
        JOIN areas ar ON s.area_id = ar.area_id
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY ar.name, month_num
        ORDER BY ar.name, month_num
    """, (f"{year}-01-01", f"{year}-12-31"))

    # Determine maximum month present in dataset
    cursor.execute("""
        SELECT MAX(CAST(strftime('%m', date) AS INTEGER))
        FROM spills
        WHERE date >= ? AND date <= ?
    """, (f"{year}-01-01", f"{year}-12-31"))
    max_month_row = cursor.fetchone()
    max_month = max_month_row[0] if (max_month_row and max_month_row[0]) else 12

    # Pre-populate all areas
    cursor.execute("SELECT name FROM areas ORDER BY area_id")
    areas = {row["name"]: [0] * max_month for row in cursor.fetchall()}

    for row in cursor.fetchall():
        a_name = row["area_name"]
        m_idx = row["month_num"] - 1
        if a_name in areas and 0 <= m_idx < max_month:
            areas[a_name][m_idx] = row["spill_count"]

    # Re-query groups to fill table
    cursor.execute("""
        SELECT ar.name as area_name,
               CAST(strftime('%m', s.date) AS INTEGER) as month_num,
               COUNT(*) as spill_count
        FROM spills s
        JOIN areas ar ON s.area_id = ar.area_id
        WHERE s.date >= ? AND s.date <= ?
        GROUP BY ar.name, month_num
    """, (f"{year}-01-01", f"{year}-12-31"))
    for row in cursor.fetchall():
        a_name = row["area_name"]
        m_idx = row["month_num"] - 1
        if a_name in areas and 0 <= m_idx < max_month:
            areas[a_name][m_idx] = row["spill_count"]

    result_areas = {}
    for a_name, m_counts in areas.items():
        result_areas[a_name] = {
            "monthly_counts": m_counts,
            "total": sum(m_counts),
        }

    if close_conn:
        conn.close()

    return {
        "year": year,
        "months": [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ][:max_month],
        "areas": result_areas,
    }
