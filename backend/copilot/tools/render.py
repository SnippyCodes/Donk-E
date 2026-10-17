from typing import Any, Dict, List, Optional


def render_status_card(
    asset_id: str,
    name: str,
    well_type: str,
    area_name: str,
    is_producing: bool,
    wellhead_temp_c: float,
    ambient_temp_c: float,
    delta_temp_c: float,
    threshold_temp_delta: float,
    recorded_status: str,
    status_is_stale: bool,
    latest_inspection_id: str,
    latest_inspected_date: str,
    inspector_name: str,
    reason_summary: str,
    evidence_ids: List[str],
) -> Dict[str, Any]:
    """Generate visual block payload for StatusCard (single well right now)."""
    return {
        "block_type": "status_card",
        "asset_id": asset_id,
        "name": name,
        "well_type": well_type,
        "area_name": area_name,
        "is_producing": is_producing,
        "metrics": {
            "wellhead_temp_c": wellhead_temp_c,
            "ambient_temp_c": ambient_temp_c,
            "delta_temp_c": delta_temp_c,
            "threshold_temp_delta": threshold_temp_delta,
        },
        "system_status": {
            "recorded_status": recorded_status,
            "status_is_stale": status_is_stale,
        },
        "latest_inspection": {
            "inspection_id": latest_inspection_id,
            "date": latest_inspected_date,
            "inspector": inspector_name,
        },
        "reason": reason_summary,
        "evidence_ids": evidence_ids,
    }


def render_table(
    title: str,
    columns: List[Dict[str, str]],
    rows: List[Dict[str, Any]],
    evidence_ids: List[str],
    summary_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate visual block payload for Table."""
    return {
        "block_type": "table",
        "title": title,
        "columns": columns,
        "rows": rows,
        "summary_stats": summary_stats or {},
        "evidence_ids": evidence_ids,
    }


def render_line_chart(
    title: str,
    x_axis: str,
    series: List[Dict[str, Any]],
    markers: Optional[List[Dict[str, Any]]] = None,
    evidence_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate visual block payload for LineChart."""
    return {
        "block_type": "line_chart",
        "title": title,
        "x_axis": x_axis,
        "series": series,
        "markers": markers or [],
        "evidence_ids": evidence_ids or [],
    }


def render_bar_chart(
    title: str,
    categories: List[str],
    values: List[float],
    unit: str,
    evidence_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate visual block payload for BarChart."""
    return {
        "block_type": "bar_chart",
        "title": title,
        "categories": categories,
        "values": values,
        "unit": unit,
        "evidence_ids": evidence_ids or [],
    }


def render_map_view(
    title: str,
    center: Dict[str, float],
    pins: List[Dict[str, Any]],
    evidence_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate visual block payload for MapView."""
    return {
        "block_type": "map_view",
        "title": title,
        "center": center,
        "pins": pins,
        "evidence_ids": evidence_ids or [],
    }


def render_heatmap(
    title: str,
    x_labels: List[str],
    y_labels: List[str],
    matrix: List[List[int]],
    totals: Optional[Dict[str, int]] = None,
    evidence_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate visual block payload for Heatmap."""
    return {
        "block_type": "heatmap",
        "title": title,
        "x_labels": x_labels,
        "y_labels": y_labels,
        "matrix": matrix,
        "totals": totals or {},
        "evidence_ids": evidence_ids or [],
    }


def render_conflict(
    title: str,
    asset_id: str,
    item: str,
    claims: List[Dict[str, Any]],
    recommendation: str,
    evidence_ids: List[str],
) -> Dict[str, Any]:
    """Generate visual block payload for Conflict resolution."""
    return {
        "block_type": "conflict",
        "title": title,
        "asset_id": asset_id,
        "item": item,
        "claims": claims,
        "recommendation": recommendation,
        "evidence_ids": evidence_ids,
    }


def render_evidence(
    title: str,
    evidence_items: List[Dict[str, Any]],
    evidence_ids: List[str],
) -> Dict[str, Any]:
    """Generate visual block payload for Evidence audit drawer/chips."""
    return {
        "block_type": "evidence",
        "title": title,
        "evidence_items": evidence_items,
        "evidence_ids": evidence_ids,
    }

