import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import shutil
from backend.copilot.config import BASE_DIR


def make_holdout_dataset(output_dir: Path = BASE_DIR / "data" / "test-data") -> None:
    """
    Generate synthetic holdout test data simulating the 2-hour final release dataset.
    Creates a new well (WELL-0201, T350) and validates multi-root ingestion.
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fleet areas.json with additional area
    fleet_dir = output_dir / "fleet"
    fleet_dir.mkdir(parents=True, exist_ok=True)
    areas_data = {
        "areas": [
            {
                "area_id": "SE-01",
                "name": "Southeast Block 1",
                "team_id": "TEAM-SE",
                "center": {"lat": 31.90, "lon": -102.40},
                "asset_ids": ["WELL-0201"],
            }
        ],
        "teams": [
            {
                "team_id": "TEAM-SE",
                "name": "Southeast Production",
                "lead_user_id": "U-101",
            }
        ],
    }
    with open(fleet_dir / "areas.json", "w", encoding="utf-8") as f:
        json.dump(areas_data, f, indent=2)

    # 2. Asset WELL-0201 metadata and records
    well_dir = output_dir / "assets" / "WELL-0201"
    well_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "asset_id": "WELL-0201",
        "name": "SE-01 Well 201",
        "asset_category": "oil_well",
        "well_type": "T350",
        "area_id": "SE-01",
        "team_id": "TEAM-SE",
        "in_charge_user_id": "U-101",
        "location": {"lat": 31.912, "lon": -102.415},
        "installed_on": "2024-01-15",
        "equipment": [
            {"equipment_id": "WELL-0201-WH", "kind": "wellhead", "model": "WH-5000"},
            {"equipment_id": "WELL-0201-PJ", "kind": "pump_jack", "model": "PJ-456"},
        ],
        "last_inspection": {
            "inspection_id": "INS-0201-0001",
            "inspected_at": "2026-10-16T10:00:00Z",
            "inspector_user_id": "U-104",
        },
        "recorded_status": "active",
    }
    with open(well_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Single inspection
    insp = {
        "inspection_id": "INS-0201-0001",
        "asset_id": "WELL-0201",
        "inspected_at": "2026-10-16T10:00:00Z",
        "inspector_user_id": "U-104",
        "method": "drone",
        "ambient_temp_c": 21.0,
        "wellhead_temp_c": 43.5,  # Delta 22.5 > 20.0 (T350 threshold) -> producing
        "spill_detected": False,
        "spill_area_pct": None,
        "spill_est_volume_bbl": None,
        "evidence_images": [],
        "notes": "Operating normally",
    }
    with open(well_dir / "inspections.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps(insp) + "\n")

    print(f"Generated holdout test dataset in {output_dir}")


if __name__ == "__main__":
    make_holdout_dataset()
