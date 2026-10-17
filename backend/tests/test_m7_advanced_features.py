import pytest
from fastapi.testclient import TestClient

from backend.copilot.db import get_connection
from backend.copilot.domain.radar import scan_proactive_fleet_risks
from backend.copilot.domain.simulator import simulate_fleet_what_if
from backend.copilot.domain.hybrid_search import HybridRRFSearchEngine, run_hybrid_search
from backend.copilot.domain.diff import get_bitemporal_audit_diff
from backend.copilot.api.main import app
from backend.copilot.agent.loop import AgentLoop


def test_proactive_fleet_risks_radar():
    """Verify Deliverable A: Proactive Autonomous Anomaly & Risk Radar."""
    conn = get_connection()
    res = scan_proactive_fleet_risks(conn=conn, thermal_margin_deg=2.5)

    summary = res["summary"]
    assert "thermal_margin_warnings_count" in summary
    assert "pre_rca_watchlist_count" in summary
    assert "stale_status_wells_count" in summary
    assert "unresolved_conflicts_count" in summary
    assert summary["fleet_risk_level"] in ("ELEVATED", "NOMINAL")

    # Verify thermal margin stall warnings
    assert summary["thermal_margin_warnings_count"] >= 1
    sample_tw = res["thermal_warnings"][0]
    assert sample_tw["asset_id"].startswith("WELL-")
    assert sample_tw["status"] == "At Risk of Stalling"
    assert len(sample_tw["evidence_ids"]) > 0

    # Verify pre-RCA watchlist (threshold - 1 repairs in 12 months)
    assert summary["pre_rca_watchlist_count"] > 0
    sample_rca = res["pre_rca_watchlist"][0]
    assert sample_rca["corrective_repairs_count"] == sample_rca["rca_threshold"] - 1

    # Verify stale status wells
    assert summary["stale_status_wells_count"] > 0

    # Verify unresolved operator conflict on INS-0101-0197
    assert summary["unresolved_conflicts_count"] >= 1
    conflicts = [c for c in res["unresolved_conflicts"] if c.get("inspection_id") == "INS-0101-0197"]
    assert len(conflicts) == 1
    assert "INS-0101-0197" in conflicts[0]["evidence_ids"]
    assert any("CTX-0101-002" in eid for eid in conflicts[0]["evidence_ids"])
    assert any("CTX-0101-003" in eid for eid in conflicts[0]["evidence_ids"])

    # Verify all evidence IDs follow strict citation schema
    for eid in res["evidence_ids"]:
        assert any(eid.startswith(prefix) for prefix in ("INS-", "MNT-", "CTX-", "LEDGER-", "DOC:"))


def test_counterfactual_what_if_simulator_ledger_immutability():
    """Verify Deliverable B: Counterfactual What-If Simulator with strict Ledger Immutability."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ledger")
    initial_ledger_count = c.fetchone()[0]

    # Scenario 1: Spill Threshold Drops from 5.0 to 3.0 bbl
    s1 = simulate_fleet_what_if(
        scenario_query="What happens if the reportable spill volume threshold in SR-01 drops to 3.0 bbl?",
        conn=conn,
    )
    assert s1["before_count"] == 36
    assert s1["after_count"] == 170
    assert s1["net_change"] == 134
    assert s1["visual"]["block_type"] == "bar_chart"
    assert len(s1["flipped_assets_sample"]) > 0

    # Scenario 2: RCA Corrective Repair Threshold Drops from 3 to 2
    s2 = simulate_fleet_what_if(
        scenario_query="What if the RCA corrective repair threshold for T350 pump jacks was set to 2?",
        conn=conn,
    )
    assert s2["before_count"] == 14
    assert s2["after_count"] == 36
    assert s2["net_change"] == 22
    assert s2["parameter_changed"] == "rca_corrective_count"

    # Scenario 3: Temperature Delta Threshold Shift
    s3 = simulate_fleet_what_if(
        scenario_query="What if T350 temperature delta threshold increased by 3.0 C?",
        conn=conn,
    )
    assert s3["before_count"] == 79
    assert s3["after_count"] == 78
    assert s3["net_change"] == -1
    assert any(item["asset_id"] == "WELL-0201" for item in s3["flipped_assets_sample"])

    # Crucial Invariant: Verify Ledger was NOT mutated by any counterfactual simulation
    c.execute("SELECT COUNT(*) FROM ledger")
    final_ledger_count = c.fetchone()[0]
    assert final_ledger_count == initial_ledger_count


def test_hybrid_rrf_search():
    """Verify Deliverable C: Hybrid Semantic + BM25 RRF Search Engine."""
    conn = get_connection()
    engine = HybridRRFSearchEngine(conn=conn)

    # 1. Exact match query
    res_exact = engine.hybrid_search("flowline integrity testing annual", limit=5)
    assert len(res_exact) > 0
    top_ids = [r["citation_id"] for r in res_exact]
    assert any("DOC:SOP-RC#2" in tid or "MNT-" in tid for tid in top_ids)

    # 2. Semantic & morphological phrasing variation
    res_semantic = run_hybrid_search("rebalanced counterweights cooler wellhead temperature", limit=5, conn=conn)
    assert res_semantic["results_count"] > 0
    assert any("DOC:OM-T" in eid for eid in res_semantic["evidence_ids"])

    # 3. Verify RRF score ordering
    scores = [r["score"] for r in res_semantic["results"]]
    assert scores == sorted(scores, reverse=True)


def test_bitemporal_state_diff():
    """Verify Deliverable D: Bi-Temporal State Diff comparing Layer 1 vs Layer 2."""
    conn = get_connection()
    diff = get_bitemporal_audit_diff(conn=conn, limit=25)

    assert diff["summary"]["total_diff_count"] > 0
    assert diff["visual"]["block_type"] == "table"
    assert len(diff["visual"]["rows"]) > 0

    # Ensure false positive spill corrections are captured
    spill_diffs = [d for d in diff["diff_entries"] if d["field_name"] == "spill_detected"]
    assert len(spill_diffs) > 0
    sample = spill_diffs[0]
    assert "False Positive" in sample["raw_ingested_value"]
    assert "Cleared" in sample["effective_runtime_value"]
    assert sample["author_user_id"] != ""
    assert sample["citation_id"].startswith("CTX-") or sample["citation_id"].startswith("INS-")


def test_api_insights_proactive():
    """Verify FastAPI GET /api/insights/proactive endpoint."""
    client = TestClient(app)
    response = client.get("/api/insights/proactive")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "thermal_warnings" in data
    assert "pre_rca_watchlist" in data
    assert data["summary"]["fleet_risk_level"] in ("ELEVATED", "NOMINAL")


def test_agent_turn_m7_features():
    """Verify AgentLoop correctly routes M7 natural language queries."""
    agent = AgentLoop()

    # Query 1: What-If simulation
    q1_res = agent.run_turn(
        "Run What-If Simulation: What happens across the fleet if reportable spill threshold drops to 3.0 bbl?",
        user_id="U-102",
    )
    assert "36" in q1_res["content"]
    assert "170" in q1_res["content"]
    assert len(q1_res["visual_blocks"]) == 1
    assert q1_res["visual_blocks"][0]["block_type"] == "bar_chart"

    # Query 2: Bi-Temporal Audit Diff
    q2_res = agent.run_turn(
        "Show Bi-Temporal Audit Diff of all runtime operator corrections vs. raw sensor data.",
        user_id="U-102",
    )
    assert len(q2_res["visual_blocks"]) == 1
    assert q2_res["visual_blocks"][0]["block_type"] == "table"

    # Query 3: Entity resolver "Well one" (fixing screenshot issue)
    q3_res = agent.run_turn(
        "can you give me the summary of Well one how is it doing",
        user_id="U-102",
    )
    assert len(q3_res["visual_blocks"]) == 1
    assert q3_res["visual_blocks"][0]["block_type"] == "status_card"
    assert q3_res["visual_blocks"][0]["asset_id"] == "WELL-0001"
