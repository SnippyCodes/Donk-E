import pytest
from fastapi.testclient import TestClient
from backend.copilot.agent.guardrails import CitationGuardrail
from backend.copilot.agent.loop import AgentLoop
from backend.copilot.api.main import app
from backend.copilot.tools.registry import TOOL_DEFINITIONS, execute_tool


def test_tool_definitions_registry():
    """Verify tool definitions and dispatch map."""
    assert len(TOOL_DEFINITIONS) >= 15
    names = [t["name"] for t in TOOL_DEFINITIONS]
    assert "get_well_status" in names
    assert "get_area_stopped_wells" in names
    assert "record_correction" in names
    assert "record_rule_override" in names
    assert "search_documentation" in names


def test_tool_execution_status():
    """Verify tool execution through registry dispatch."""
    res = execute_tool("get_well_status", {"well_id": "WELL-0001"})
    assert res.get("data", {}).get("asset_id") == "WELL-0001"
    assert "is_producing" in res.get("data", {})
    assert "evidence_ids" in res
    assert "visual" in res
    assert res["visual"]["block_type"] == "status_card"


def test_citation_guardrail():
    """Verify Rule 6: Verified Citations Only."""
    guard = CitationGuardrail(strip_invalid=True)
    allowed = ["INS-0001-0203", "DOC:OM-T200#9.3"]

    # Valid citation
    text_valid = "Well is down according to [INS-0001-0203] and manual [DOC:OM-T200#9.3]."
    audit1 = guard.audit(text_valid, allowed)
    assert audit1["is_valid"] is True
    assert set(audit1["valid_citations"]) == set(allowed)

    # Hallucinated citation
    text_invalid = "Well is down [INS-0001-0203] due to bogus [INS-9999-9999] and [DOC:FAKE#1]."
    audit2 = guard.audit(text_invalid, allowed)
    assert audit2["is_valid"] is False
    assert "INS-9999-9999" in audit2["invalid_citations"]
    assert "DOC:FAKE#1" in audit2["invalid_citations"]
    # Verify stripped
    assert "[INS-9999-9999]" not in audit2["cleaned_text"]
    assert "[DOC:FAKE#1]" not in audit2["cleaned_text"]
    assert "[INS-0001-0203]" in audit2["cleaned_text"]


def test_agent_loop_q1():
    """Verify agent loop on Golden Q1 query."""
    loop = AgentLoop()
    res = loop.run_turn(
        message="Is WELL-0001 producing oil right now? Show me its status card.",
        user_id="U-102",
    )
    assert "content" in res
    assert len(res["visual_blocks"]) >= 1
    assert res["visual_blocks"][0]["block_type"] == "status_card"
    assert "INS-0001-0203" in res["evidence_ids"]
    assert res["user_id"] == "U-102"


def test_agent_loop_q2():
    """Verify agent loop on Golden Q2 query."""
    loop = AgentLoop()
    res = loop.run_turn(
        message="Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.",
        user_id="U-102",
    )
    assert "content" in res
    assert len(res["visual_blocks"]) >= 1
    assert res["visual_blocks"][0]["block_type"] == "table"
    assert any("INS-0164-0205" in eid for eid in res["evidence_ids"])


def test_api_health():
    """Test /api/health endpoint."""
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["counts"]["assets"] > 0
    assert data["counts"]["inspections"] > 0


def test_api_users():
    """Test /api/users endpoint."""
    client = TestClient(app)
    resp = client.get("/api/users")
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) > 0
    user_ids = [u["user_id"] for u in users]
    assert "U-101" in user_ids
    assert "U-102" in user_ids


def test_api_chat():
    """Test /api/chat endpoint."""
    client = TestClient(app)
    resp = client.post(
        "/api/chat",
        json={"message": "Is WELL-0001 producing oil right now?", "user_id": "U-102"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "visual_blocks" in data
    assert len(data["visual_blocks"]) > 0
    assert data["user_id"] == "U-102"
    assert "agent_trace" in data
    assert "tools_invoked" in data["agent_trace"]


def test_openrouter_gemma_client():
    """Verify OpenRouter Gemma 4 client initialization and fallback robustness."""
    from backend.copilot.agent.llm import LLMClient
    client = LLMClient(provider="openrouter", model="google/gemma-4-26b-a4b-it:free")
    assert client.provider == "openrouter"
    assert "gemma-4" in client.model

    # Test local fallback execution
    res = client.chat_completion([{"role": "user", "content": "Is WELL-0001 producing oil right now?"}])
    assert "tool_calls" in res
    assert len(res["tool_calls"]) > 0
    assert res["tool_calls"][0]["name"] == "get_well_status"


def test_api_admin_ingest():
    """Verify POST /api/admin/ingest hot-reloads dataset idempotently."""
    client = TestClient(app)
    resp = client.post("/api/admin/ingest", json={"data_roots": ["data/sample-data"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["wells_loaded"] > 0
    assert data["inspections_loaded"] > 0
    assert "elapsed_ms" in data
    assert "data_end" in data


def test_api_vision_check():
    """Verify POST /api/vision/check extracts visual findings and evaluates claim."""
    client = TestClient(app)
    resp = client.post(
        "/api/vision/check",
        json={
            "well_id": "WELL-0164",
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "user_id": "U-102",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["well_id"] == "WELL-0164"
    assert "observation" in data
    assert "claim_verdict" in data

