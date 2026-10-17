import pytest
import yaml
from pathlib import Path

from backend.copilot.config import BASE_DIR
from backend.copilot.db import get_connection
from backend.copilot.ingest.loader import load_dataset
from backend.copilot.tools.analytics import (
    tool_get_well_status,
    tool_get_area_stopped_wells,
    tool_get_well_temperature_trend,
    tool_get_well_spills_summary,
    tool_get_well_downtime,
    tool_get_area_top_downtime,
    tool_get_area_spills_map,
    tool_get_spills_heatmap,
    tool_get_well_compliance_audit,
    tool_get_uncontained_spills,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure test database is fully loaded before running golden tests."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM well_now")
    cnt = c.fetchone()[0]
    conn.close()
    if cnt < 200:
        load_dataset()


@pytest.fixture(scope="session")
def golden_spec():
    """Load golden test specifications from tests/golden_cases.yaml."""
    yaml_path = BASE_DIR / "tests" / "golden_cases.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


def test_q1_well_status(golden_spec):
    """Q1: Is WELL-0001 producing oil right now? Status card."""
    spec = golden_spec["Q1"]
    res = tool_get_well_status("WELL-0001")
    assert "error" not in res, res.get("error")

    data = res["data"]
    assert data["is_producing"] == 0
    assert data["latest_inspection_id"] == spec["expected"]["latest_inspection_id"]
    assert data["latest_inspected_date"] == spec["expected"]["inspected_date"]
    assert data["inspector_name"] == spec["expected"]["inspector_name"]
    assert data["method"] == spec["expected"]["method"]
    assert data["delta_temp_c"] == spec["expected"]["delta_temp_c"]
    exp_thresh = spec["expected"].get("threshold_temp_delta", spec["expected"].get("threshold_delta_c"))
    assert data["threshold_temp_delta"] == exp_thresh
    assert data["recorded_status"] == spec["expected"]["recorded_status"]
    assert data["status_is_stale"] == 1
    assert data["reason_ref_id"] == spec["expected"]["reason_note_id"]
    assert "rod string" in data["reason_summary"].lower()

    visual = res["visual"]
    assert visual["block_type"] == "status_card"
    assert visual["asset_id"] == "WELL-0001"
    assert visual["is_producing"] is False


def test_q2_area_stopped_wells(golden_spec):
    """Q2: Which wells in Northeast Block 8 are not producing oil right now? Table."""
    spec = golden_spec["Q2"]
    res = tool_get_area_stopped_wells("Northeast Block 8")
    assert "error" not in res

    assert res["count"] == spec["expected"]["count"]
    wells_map = {w["well_id"]: w for w in res["wells"]}

    # Verify all 4 expected wells are present
    for exp_id, exp_info in spec["expected"]["wells"].items():
        assert exp_id in wells_map, f"Expected {exp_id} in stopped wells"
        w_res = wells_map[exp_id]

        # Verify reason characteristics
        if exp_info["reason_type"] == "no_recorded_reason":
            assert "no recorded reason" in w_res["reason"].lower()
            if exp_info.get("inspector_note"):
                assert exp_info["inspector_note"] in w_res["reason"]
        elif exp_info["reason_type"] == "repair":
            assert exp_info["repair_id"] in w_res["reason"]

    visual = res["visual"]
    assert visual["block_type"] == "table"
    assert len(visual["rows"]) == 4


def test_q3_temperature_trend(golden_spec):
    """Q3: WELL-0001 wellhead vs ambient temperature over last 13 weeks. Line chart."""
    spec = golden_spec["Q3"]
    res = tool_get_well_temperature_trend("WELL-0001", "last 13 weeks")
    assert "error" not in res

    assert res["readings_count"] == spec["expected"]["readings_count"]
    assert res["window"]["start_date"] == spec["expected"]["start_date"]
    assert res["window"]["end_date"] == spec["expected"]["end_date"]
    assert res["non_producing_dates"] == spec["expected"]["non_producing_dates"]

    visual = res["visual"]
    assert visual["block_type"] == "line_chart"
    assert len(visual["markers"]) == 2


def test_q4_spills_summary(golden_spec):
    """Q4: WELL-0001 spills in last 4 years. Table."""
    spec = golden_spec["Q4"]
    res = tool_get_well_spills_summary("WELL-0001", "last 4 years")
    assert "error" not in res

    assert res["total_detections"] == spec["expected"]["total_detections"]
    assert res["corrected_detections"] == spec["expected"]["corrected_detections"]
    assert res["real_spills_count"] == spec["expected"]["real_spills_count"]
    assert res["total_volume_bbl"] == spec["expected"]["total_volume_bbl"]

    # Check spill dates
    exp_dates = [s["date"] for s in spec["expected"]["spills"]]
    actual_dates = [s["date"] for s in res["spills"]]
    assert actual_dates == exp_dates

    visual = res["visual"]
    assert visual["block_type"] == "table"
    assert len(visual["rows"]) == 6


def test_q5_well_downtime(golden_spec):
    """Q5: WELL-0001 downtime days in 2025."""
    spec = golden_spec["Q5"]
    res = tool_get_well_downtime("WELL-0001", "2025")

    assert res["downtime_days"] == spec["expected"]["downtime_days"]
    assert res["down_inspections_count"] == spec["expected"]["down_inspections_count"]

    exp_dates = [i["date"] for i in spec["expected"]["inspections"]]
    actual_dates = [i["date"] for i in res["inspections"]]
    assert actual_dates == exp_dates

    # Check repair causes
    causes = [i["cause_repair_id"] for i in res["inspections"]]
    assert "MNT-0001-021" in causes
    assert "MNT-0001-023" in causes


def test_q6_area_top_downtime(golden_spec):
    """Q6: Top 3 wells by downtime in Northeast Block 7 in last 4 months. Bar chart."""
    spec = golden_spec["Q6"]
    res = tool_get_area_top_downtime("Northeast Block 7", "last 4 months", 3)
    assert "error" not in res

    assert res["window"]["start_date"] == spec["expected"]["window_start"]
    assert res["window"]["end_date"] == spec["expected"]["window_end"]

    top_3 = res["top_wells"]
    assert len(top_3) == 3
    assert top_3[0]["well_id"] == "WELL-0121"
    assert top_3[0]["downtime_days"] == 49
    assert top_3[0]["well_type"] == "T200"

    assert top_3[1]["well_id"] in ["WELL-0138", "WELL-0107"]
    assert top_3[1]["downtime_days"] == 42
    assert top_3[2]["well_id"] in ["WELL-0138", "WELL-0107"]
    assert top_3[2]["downtime_days"] == 42

    assert res["runner_up"]["well_id"] == "WELL-0119"
    assert res["runner_up"]["downtime_days"] == 28

    visual = res["visual"]
    assert visual["block_type"] == "bar_chart"
    assert len(visual["categories"]) == 3


def test_q7_area_spills_map(golden_spec):
    """Q7: Real spills in Northeast Block 8 in last 90 days. Map."""
    spec = golden_spec["Q7"]
    res = tool_get_area_spills_map("Northeast Block 8", "last 90 days")
    assert "error" not in res

    assert res["count"] == spec["expected"]["count"]
    pins_by_well = {p["well_id"]: p for p in res["pins"]}

    for exp_pin in spec["expected"]["pins"]:
        w_id = exp_pin["well_id"]
        assert w_id in pins_by_well
        actual = pins_by_well[w_id]
        assert actual["date"] == exp_pin["date"]
        assert actual["volume_bbl"] == exp_pin["volume_bbl"]
        assert abs(actual["lat"] - exp_pin["lat"]) < 0.001
        assert abs(actual["lon"] - exp_pin["lon"]) < 0.001

    visual = res["visual"]
    assert visual["block_type"] == "map_view"
    assert len(visual["pins"]) == 4


def test_q8_spills_heatmap(golden_spec):
    """Q8: 2026 spills heatmap by area and month."""
    spec = golden_spec["Q8"]
    res = tool_get_spills_heatmap("2026")

    for a_name, a_exp in spec["expected"]["areas"].items():
        assert a_name in res["areas"], f"Expected {a_name} in heatmap"
        a_act = res["areas"][a_name]
        assert a_act["total"] == a_exp["total"], f"Total mismatch for {a_name}"
        assert a_act["monthly_counts"] == a_exp["monthly_counts"], f"Monthly mismatch for {a_name}"

    visual = res["visual"]
    assert visual["block_type"] == "heatmap"


def test_q9_compliance_audit(golden_spec):
    """Q9: WELL-0001 compliance audit over last 12 months. Table."""
    spec = golden_spec["Q9"]
    res = tool_get_well_compliance_audit("WELL-0001", "last 12 months")

    assert res["breaches_count"] == spec["expected"]["breaches_count"]
    assert res["total_open_fines_usd"] == spec["expected"]["total_open_fines_usd"]

    protocols = [b["protocol_id"] for b in res["breaches"]]
    assert "SR-01" in protocols
    assert "SR-02" in protocols
    assert "SR-03" in protocols
    assert "RC-04" in protocols

    # Check pending actions
    items = [p["item"] for p in res["pending_actions"]]
    assert "flowline_rca" in items
    assert "planned_shutin_unrecorded" in items

    # Check rules met
    met_protos = [r["protocol_id"] for r in res["rules_met"]]
    assert "RC-02" in met_protos

    visual = res["visual"]
    assert visual["block_type"] == "table"


def test_q10_uncontained_spills(golden_spec):
    """Q10: Southwest Block 24 spills not contained within SOP limit (4 hours). Table."""
    spec = golden_spec["Q10"]
    res = tool_get_uncontained_spills("Southwest Block 24", "last 90 days", 4.0)
    assert "error" not in res

    assert res["count"] == spec["expected"]["count"]
    wells_map = {it["well_id"]: it for it in res["items"]}

    for exp_it in spec["expected"]["items"]:
        w_id = exp_it["well_id"]
        assert w_id in wells_map
        act = wells_map[w_id]
        assert act["contained_hours"] == exp_it["contained_hours"]
        assert act["report_id"] == exp_it["report_id"]
        assert act["inspection_id"] == exp_it["inspection_id"]

    visual = res["visual"]
    assert visual["block_type"] == "table"
    assert len(visual["rows"]) == 2
