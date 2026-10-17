import os
from pathlib import Path
from backend.copilot.config import BASE_DIR, get_dataset_roots
from backend.copilot.db import get_connection
from backend.copilot.ingest.loader import load_dataset
from backend.copilot.resolver import get_data_end
from backend.copilot.tools.registry import execute_tool
from scripts.make_holdout import make_holdout_dataset


def test_holdout_multiroot_ingest():
    """Verify that dropping a new test-data root loads new wells and respects dynamic DATA_END."""
    test_data_dir = BASE_DIR / "data" / "test-data"
    make_holdout_dataset(output_dir=test_data_dir)
    assert test_data_dir.exists()

    sample_data_dir = BASE_DIR / "data" / "sample-data"
    roots = [sample_data_dir, test_data_dir]
    valid_roots = [r for r in roots if r.exists()]
    assert len(valid_roots) >= 1

    # Ingest multi-root
    counts = load_dataset(roots=valid_roots)
    assert counts["assets"] > 0
    assert counts["inspections"] > 0

    # Verify new well WELL-0201 is present
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT asset_id, well_type FROM assets WHERE asset_id = 'WELL-0201'")
        row = c.fetchone()
        assert row is not None
        assert row[0] == "WELL-0201"
        assert row[1] == "T350"

        # Verify dynamic DATA_END auto-advances or matches max inspection
        data_end = get_data_end(conn)
        assert data_end >= "2026-10-16"
    finally:
        conn.close()

    # Query status of WELL-0201 via tool
    res = execute_tool("get_well_status", {"well_id": "WELL-0201"})
    assert res.get("data", {}).get("asset_id") == "WELL-0201"
    assert "visual" in res
    assert res["visual"]["block_type"] == "status_card"
