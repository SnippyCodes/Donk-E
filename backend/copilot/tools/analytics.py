import sqlite3
from typing import Any, Dict, List, Optional

from backend.copilot.db import get_connection
from backend.copilot.resolver import EntityResolver, resolve_window
from backend.copilot.domain.downtime import calculate_well_downtime, get_area_downtime_ranking
from backend.copilot.domain.spills import get_well_spills, get_area_spills_map, get_spills_heatmap
from backend.copilot.domain.compliance import evaluate_well_compliance, get_uncontained_spills
from backend.copilot.tools.render import (
    render_status_card,
    render_table,
    render_line_chart,
    render_bar_chart,
    render_map_view,
    render_heatmap,
)


def tool_get_well_status(well_id: str, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Q1: Return status card for a well right now."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    norm_id = resolver.resolve_well_id(well_id) or well_id

    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.*, ar.name as area_name
        FROM well_now w
        JOIN areas ar ON w.area_id = ar.area_id
        WHERE w.asset_id = ?
    """, (norm_id,))
    row = cursor.fetchone()

    if not row:
        if close_conn:
            conn.close()
        return {"error": f"Well {norm_id} not found."}

    w = dict(row)
    evidence_ids = [w["latest_inspection_id"]]
    if w["reason_ref_id"]:
        evidence_ids.append(w["reason_ref_id"])
    evidence_ids.append(f"DOC:OM-{w['well_type']}#9.3")

    visual = render_status_card(
        asset_id=w["asset_id"],
        name=w["name"],
        well_type=w["well_type"],
        area_name=w["area_name"],
        is_producing=bool(w["is_producing"]),
        wellhead_temp_c=w["wellhead_temp_c"],
        ambient_temp_c=w["ambient_temp_c"],
        delta_temp_c=w["delta_temp_c"],
        threshold_temp_delta=w["threshold_temp_delta"],
        recorded_status=w["recorded_status"],
        status_is_stale=bool(w["status_is_stale"]),
        latest_inspection_id=w["latest_inspection_id"],
        latest_inspected_date=w["latest_inspected_date"],
        inspector_name=w["inspector_name"] or w["inspector_user_id"],
        reason_summary=w["reason_summary"],
        evidence_ids=evidence_ids,
    )

    if close_conn:
        conn.close()

    return {
        "data": w,
        "visual": visual,
        "evidence_ids": evidence_ids,
        **w,
    }


def tool_get_area_stopped_wells(area_query: str, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Q2: Return table of non-producing wells in an area right now."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    area = resolver.resolve_area(area_query)
    if not area:
        if close_conn:
            conn.close()
        return {"error": f"Area '{area_query}' not recognized."}

    area_id = area["area_id"]
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.asset_id, w.delta_temp_c, w.recorded_status, w.status_is_stale,
               w.reason_type, w.reason_ref_id, w.reason_summary, w.inspector_note,
               w.latest_inspection_id, w.latest_inspected_date
        FROM well_now w
        WHERE w.area_id = ?
          AND w.is_producing = 0
        ORDER BY w.asset_id ASC
    """, (area_id,))
    rows = cursor.fetchall()

    table_rows = []
    evidence_ids = []
    for r in rows:
        w_dict = dict(r)
        evidence_ids.append(r["latest_inspection_id"])
        if r["reason_ref_id"]:
            evidence_ids.append(r["reason_ref_id"])

        table_rows.append({
            "well_id": r["asset_id"],
            "wellhead_above_air": f"{r['delta_temp_c']} °C",
            "recorded_status": f"{r['recorded_status']} (out of date)" if r["status_is_stale"] else r["recorded_status"],
            "reason": r["reason_summary"],
            "latest_inspection_date": r["latest_inspected_date"],
        })

    columns = [
        {"key": "well_id", "label": "Well"},
        {"key": "wellhead_above_air", "label": "Wellhead above air"},
        {"key": "recorded_status", "label": "Recorded status"},
        {"key": "reason", "label": "Reason"},
    ]

    visual = render_table(
        title=f"Non-Producing Wells in {area['name']}",
        columns=columns,
        rows=table_rows,
        evidence_ids=list(set(evidence_ids)),
        summary_stats={"non_producing_count": len(table_rows)},
    )

    if close_conn:
        conn.close()

    return {
        "area_id": area_id,
        "area_name": area["name"],
        "count": len(table_rows),
        "wells": table_rows,
        "visual": visual,
        "evidence_ids": list(set(evidence_ids)),
    }


def tool_get_well_temperature_trend(
    well_id: str,
    window_expr: str = "last 13 weeks",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q3: Return line chart of wellhead temp vs ambient temp over time."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    norm_id = resolver.resolve_well_id(well_id) or well_id
    start_date, end_date = resolve_window(window_expr, conn)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT inspected_date, effective_wellhead_temp_c as wellhead_temp_c, ambient_temp_c, delta_temp_c,
               threshold_temp_delta, is_producing, inspection_id
        FROM eff_inspection
        WHERE asset_id = ?
          AND inspected_date >= ?
          AND inspected_date <= ?
        ORDER BY inspected_date ASC
    """, (norm_id, start_date, end_date))
    rows = cursor.fetchall()

    dates = []
    wht_series = []
    amb_series = []
    non_producing_dates = []
    evidence_ids = []

    for r in rows:
        dt = r["inspected_date"]
        dates.append(dt)
        wht_series.append(r["wellhead_temp_c"])
        amb_series.append(r["ambient_temp_c"])
        evidence_ids.append(r["inspection_id"])
        if r["is_producing"] == 0:
            non_producing_dates.append(dt)

    # Threshold citation
    cursor.execute("SELECT well_type FROM assets WHERE asset_id = ?", (norm_id,))
    wtype = cursor.fetchone()[0]
    evidence_ids.append(f"DOC:OM-{wtype}#9.3")

    markers = [{"date": d, "label": "Not Producing Oil"} for d in non_producing_dates]

    visual = render_line_chart(
        title=f"{norm_id} Temperature Trend ({window_expr}: {start_date} to {end_date})",
        x_axis="Date",
        series=[
            {"name": "Wellhead Temperature (°C)", "data": wht_series, "dates": dates},
            {"name": "Ambient Air Temperature (°C)", "data": amb_series, "dates": dates},
        ],
        markers=markers,
        evidence_ids=evidence_ids,
    )

    if close_conn:
        conn.close()

    return {
        "well_id": norm_id,
        "window": {"start_date": start_date, "end_date": end_date},
        "readings_count": len(rows),
        "non_producing_dates": non_producing_dates,
        "visual": visual,
        "evidence_ids": evidence_ids,
    }


def tool_get_well_spills_summary(
    well_id: str,
    window_expr: str = "last 4 years",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q4: Return table of oil spills for a well over a date window."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    norm_id = resolver.resolve_well_id(well_id) or well_id
    start_date, end_date = resolve_window(window_expr, conn)

    spills_data = get_well_spills(norm_id, start_date, end_date, conn)

    table_rows = []
    evidence_ids = []
    for s in spills_data["spills"]:
        evidence_ids.append(s["inspection_id"])
        table_rows.append({
            "date": s["date"],
            "volume_bbl": f"{s['volume_bbl']} bbl",
            "pad_area_pct": f"{s['pad_area_pct']}%" if s["pad_area_pct"] else "N/A",
            "inspection_id": s["inspection_id"],
        })

    for c in spills_data["corrections"]:
        evidence_ids.append(c["note_id"])

    columns = [
        {"key": "date", "label": "Inspection Date"},
        {"key": "volume_bbl", "label": "Crude Volume"},
        {"key": "pad_area_pct", "label": "Pad Area"},
        {"key": "inspection_id", "label": "Inspection ID"},
    ]

    visual = render_table(
        title=f"Oil Spills for {norm_id} ({window_expr})",
        columns=columns,
        rows=table_rows,
        evidence_ids=evidence_ids,
        summary_stats={
            "real_spills_count": spills_data["real_spills_count"],
            "total_volume_bbl": spills_data["total_volume_bbl"],
            "false_positives_excluded": spills_data["corrected_detections"],
        },
    )

    if close_conn:
        conn.close()

    return {
        **spills_data,
        "visual": visual,
        "evidence_ids": evidence_ids,
    }


def tool_get_well_downtime(
    well_id: str,
    window_expr: str = "2025",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q5: Calculate downtime days for a well in a period."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    norm_id = resolver.resolve_well_id(well_id) or well_id
    start_date, end_date = resolve_window(window_expr, conn)

    dt_data = calculate_well_downtime(norm_id, start_date, end_date, conn)

    evidence_ids = []
    for insp in dt_data["inspections"]:
        evidence_ids.append(insp["inspection_id"])
        if insp["cause_repair_id"]:
            evidence_ids.append(insp["cause_repair_id"])

    if close_conn:
        conn.close()

    return {
        **dt_data,
        "evidence_ids": list(set(evidence_ids)),
    }


def tool_get_area_top_downtime(
    area_query: str,
    window_expr: str = "last 4 months",
    top_n: int = 3,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q6: Return bar chart of top downtime wells in an area."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    area = resolver.resolve_area(area_query)
    if not area:
        if close_conn:
            conn.close()
        return {"error": f"Area '{area_query}' not recognized."}

    start_date, end_date = resolve_window(window_expr, conn)
    ranking = get_area_downtime_ranking(area["area_id"], start_date, end_date, top_n, conn)

    categories = [f"{w['well_id']} ({w['well_type']})" for w in ranking["top_wells"]]
    values = [float(w["downtime_days"]) for w in ranking["top_wells"]]

    visual = render_bar_chart(
        title=f"Top {top_n} Wells by Downtime in {area['name']} ({start_date} to {end_date})",
        categories=categories,
        values=values,
        unit="Days",
    )

    if close_conn:
        conn.close()

    return {
        "area_id": area["area_id"],
        "area_name": area["name"],
        "window": {"start_date": start_date, "end_date": end_date},
        "top_wells": ranking["top_wells"],
        "runner_up": ranking["runner_up"],
        "visual": visual,
    }


def tool_get_area_spills_map(
    area_query: str,
    window_expr: str = "last 90 days",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q7: Return map of real spills in an area during a date window."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    area = resolver.resolve_area(area_query)
    if not area:
        if close_conn:
            conn.close()
        return {"error": f"Area '{area_query}' not recognized."}

    start_date, end_date = resolve_window(window_expr, conn)
    map_data = get_area_spills_map(area["area_id"], start_date, end_date, conn)

    # Get area center
    cursor = conn.cursor()
    cursor.execute("SELECT center_lat, center_lon FROM areas WHERE area_id = ?", (area["area_id"],))
    c_row = cursor.fetchone()
    center = {"lat": c_row[0] or 32.15, "lon": c_row[1] or -102.16}

    pins = [
        {
            "id": p["spill_id"],
            "title": f"{p['well_id']} ({p['date']})",
            "lat": p["lat"],
            "lon": p["lon"],
            "details": f"{p['volume_bbl']} bbl crude",
            "inspection_id": p["inspection_id"],
        }
        for p in map_data["pins"]
    ]

    evidence_ids = [p["inspection_id"] for p in map_data["pins"]]

    visual = render_map_view(
        title=f"Oil Spills in {area['name']} ({start_date} to {end_date})",
        center=center,
        pins=pins,
        evidence_ids=evidence_ids,
    )

    if close_conn:
        conn.close()

    return {
        "area_id": area["area_id"],
        "area_name": area["name"],
        "count": map_data["count"],
        "pins": map_data["pins"],
        "visual": visual,
        "evidence_ids": evidence_ids,
    }


def tool_get_spills_heatmap(
    year: str = "2026",
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q8: Return heatmap of spills across areas and months for a calendar year."""
    matrix_data = get_spills_heatmap(year, conn)

    x_labels = matrix_data["months"]
    y_labels = list(matrix_data["areas"].keys())
    matrix = [matrix_data["areas"][y]["monthly_counts"] for y in y_labels]
    totals = {y: matrix_data["areas"][y]["total"] for y in y_labels}

    visual = render_heatmap(
        title=f"{year} Oil Spills by Geographic Area and Month",
        x_labels=x_labels,
        y_labels=y_labels,
        matrix=matrix,
        totals=totals,
    )

    return {
        **matrix_data,
        "visual": visual,
    }


def tool_get_well_compliance_audit(
    well_id: str,
    window_expr: str = "last 12 months",
    conn: Optional[sqlite3.Connection] = None,
    window: Optional[str] = None,
) -> Dict[str, Any]:
    """Q9: Return compliance breaches, open violations, pending actions, and met rules."""
    if window is not None:
        window_expr = window

    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    norm_id = resolver.resolve_well_id(well_id) or well_id
    start_date, end_date = resolve_window(window_expr, conn)

    audit = evaluate_well_compliance(norm_id, start_date, end_date, conn)

    evidence_ids = []
    for b in audit["breaches"]:
        if b.get("event_id"):
            evidence_ids.append(b["event_id"])
        if b.get("nov_event_id"):
            evidence_ids.append(b["nov_event_id"])
        if b.get("report_id"):
            evidence_ids.append(b["report_id"])
        if b.get("inspection_id"):
            evidence_ids.append(b["inspection_id"])

    for a in audit["pending_actions"]:
        if a.get("note_id"):
            evidence_ids.append(a["note_id"])
        for m in a.get("repairs", []):
            evidence_ids.append(m)

    for r in audit["rules_met"]:
        if r.get("maintenance_id"):
            evidence_ids.append(r["maintenance_id"])

    # Build table rows for visual display
    table_rows = []
    for b in audit["breaches"]:
        table_rows.append({
            "protocol": b["protocol_id"],
            "type": "Breach",
            "detail": b["description"],
            "fine": f"${b.get('fine_usd', 0):,.0f}" if b.get("fine_usd") else "None",
            "status": b.get("fine_status") or b.get("status") or "Breached",
        })

    for p in audit["pending_actions"]:
        table_rows.append({
            "protocol": p.get("equipment", "Operation").upper(),
            "type": "Action Required",
            "detail": p["description"],
            "fine": "N/A",
            "status": "Pending",
        })

    for m in audit["rules_met"]:
        table_rows.append({
            "protocol": m["protocol_id"],
            "type": "Compliant",
            "detail": m["description"],
            "fine": "$0",
            "status": "Met",
        })

    columns = [
        {"key": "protocol", "label": "Protocol / Item"},
        {"key": "type", "label": "Type"},
        {"key": "detail", "label": "Detail"},
        {"key": "fine", "label": "Fine USD"},
        {"key": "status", "label": "Status"},
    ]

    visual = render_table(
        title=f"Compliance Audit for {norm_id} ({start_date} to {end_date})",
        columns=columns,
        rows=table_rows,
        evidence_ids=list(set(evidence_ids)),
        summary_stats={
            "breaches_count": audit["breaches_count"],
            "open_fines_usd": audit["total_open_fines_usd"],
            "pending_actions_count": len(audit["pending_actions"]),
        },
    )

    if close_conn:
        conn.close()

    return {
        **audit,
        "visual": visual,
        "evidence_ids": list(set(evidence_ids)),
    }


def tool_get_uncontained_spills(
    area_query: str,
    window_expr: str = "last 90 days",
    limit_hours: float = 4.0,
    conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Q10: Return table of spills exceeding containment time limit."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    area = resolver.resolve_area(area_query)
    if not area:
        if close_conn:
            conn.close()
        return {"error": f"Area '{area_query}' not recognized."}

    start_date, end_date = resolve_window(window_expr, conn)
    res = get_uncontained_spills(area["area_id"], start_date, end_date, limit_hours, conn)

    table_rows = []
    evidence_ids = []
    for it in res["items"]:
        evidence_ids.append(it["inspection_id"])
        if it["report_id"]:
            evidence_ids.append(it["report_id"])

        table_rows.append({
            "well_id": it["well_id"],
            "date": it["date"],
            "volume_bbl": f"{it['volume_bbl']} bbl",
            "contained_hours": f"{it['contained_hours']} hours",
            "report_id": it["report_id"],
            "inspection_id": it["inspection_id"],
        })

    columns = [
        {"key": "well_id", "label": "Well"},
        {"key": "date", "label": "Date"},
        {"key": "volume_bbl", "label": "Volume"},
        {"key": "contained_hours", "label": "Containment Time"},
        {"key": "report_id", "label": "Report ID"},
    ]

    visual = render_table(
        title=f"Spills Exceeding {limit_hours}h Containment in {area['name']} ({start_date} to {end_date})",
        columns=columns,
        rows=table_rows,
        evidence_ids=list(set(evidence_ids)),
        summary_stats={"uncontained_count": res["count"]},
    )

    if close_conn:
        conn.close()

    return {
        "area_id": area["area_id"],
        "area_name": area["name"],
        "window": {"start_date": start_date, "end_date": end_date},
        "count": res["count"],
        "items": res["items"],
        "visual": visual,
        "evidence_ids": list(set(evidence_ids)),
    }


def tool_get_proactive_fleet_risks(
    thermal_margin_deg: float = 2.5,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """M7 Deliverable A: Proactive Autonomous Anomaly & Risk Radar."""
    from backend.copilot.domain.radar import scan_proactive_fleet_risks
    return scan_proactive_fleet_risks(conn=conn, thermal_margin_deg=thermal_margin_deg)


def tool_simulate_fleet_what_if(
    scenario_query: Optional[str] = None,
    scenario_type: Optional[str] = None,
    target_well_type: Optional[str] = None,
    simulated_value: Optional[float] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """M7 Deliverable B: Counterfactual What-If Fleet Simulator."""
    from backend.copilot.domain.simulator import simulate_fleet_what_if
    return simulate_fleet_what_if(
        scenario_query=scenario_query,
        scenario_type=scenario_type,
        target_well_type=target_well_type,
        simulated_value=simulated_value,
        conn=conn,
    )


def tool_get_bitemporal_audit_diff(
    limit: int = 50,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """M7 Deliverable D: Bi-Temporal State Diff (Raw Sensors vs Ledger Overlay)."""
    from backend.copilot.domain.diff import get_bitemporal_audit_diff
    return get_bitemporal_audit_diff(conn=conn, limit=limit)


def tool_get_well_equipment_and_maintenance(
    well_id: str,
    limit: int = 10,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Retrieve installed equipment specs and maintenance work history for a well."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    resolver = EntityResolver(conn)
    norm_id = resolver.resolve_well_id(well_id) or well_id

    cursor = conn.cursor()
    cursor.execute("SELECT asset_id, name, well_type, area_id FROM assets WHERE asset_id = ?", (norm_id,))
    asset_row = cursor.fetchone()
    if not asset_row:
        if close_conn:
            conn.close()
        return {"error": f"Well {norm_id} not found."}

    cursor.execute("""
        SELECT equipment_id, kind, model
        FROM equipment
        WHERE asset_id = ?
        ORDER BY kind ASC
    """, (norm_id,))
    equipment = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT maintenance_id, equipment_kind, started_at, completed_at,
               issue, action_taken, maintenance_type, downtime_hours, report_file
        FROM maintenance
        WHERE asset_id = ?
        ORDER BY started_at DESC
        LIMIT ?
    """, (norm_id, limit))
    maintenance = [dict(r) for r in cursor.fetchall()]

    evidence_ids = [eq["equipment_id"] for eq in equipment] + [m["maintenance_id"] for m in maintenance]

    table_rows = []
    for eq in equipment:
        latest_job = next((m for m in maintenance if m["equipment_kind"] == eq["kind"]), None)
        table_rows.append({
            "Equipment Kind": eq["kind"],
            "Model / Specs": eq["model"],
            "Latest Job": latest_job["issue"] if latest_job else "No recent work",
            "Started At": latest_job["started_at"][:16].replace("T", " ") if latest_job else "N/A",
            "Evidence": f"[{latest_job['maintenance_id']}]" if latest_job else "Asset Record",
        })

    visual = {
        "block_type": "table",
        "title": f"Installed Equipment & Maintenance History for {norm_id} ({asset_row['name']})",
        "columns": ["Equipment Kind", "Model / Specs", "Latest Job", "Started At", "Evidence"],
        "rows": table_rows,
    }

    if close_conn:
        conn.close()

    return {
        "asset_id": norm_id,
        "name": asset_row["name"],
        "well_type": asset_row["well_type"],
        "equipment": equipment,
        "maintenance_history": maintenance,
        "evidence_ids": evidence_ids,
        "visual": visual,
    }


