from types import SimpleNamespace

from backend.copilot.db import get_connection, init_db
from backend.copilot.tools.registry import execute_tool
from src.memory.recall import record_turn


class FakeMem0Client:
    def __init__(self):
        self.add_calls = []
        self.search_calls = []
        self.memories = {}

    def add(self, messages, user_id):
        self.add_calls.append((messages, user_id))
        self.memories.setdefault(user_id, []).extend(messages)
        return {"results": []}

    def search(self, query, user_id):
        self.search_calls.append((query, user_id))
        return {
            "results": [
                {"memory": item["content"], "user_id": user_id}
                for item in self.memories.get(user_id, [])
                if query.lower() in item["content"].lower()
            ]
        }


def test_mem0_adapter_scopes_add_and_search_by_user_id():
    from src.memory.mem0_adapter import Mem0Adapter

    client = FakeMem0Client()
    adapter = Mem0Adapter(memory=client)
    conn = get_connection(":memory:")
    init_db(conn)

    adapter.add([{"role": "user", "content": "Michael discussed WELL-0121"}], user_id="U-201")
    adapter.add([{"role": "user", "content": "Jessica discussed WELL-0777"}], user_id="U-202")

    michael_results = adapter.search("WELL-", user_id="U-201", conn=conn)
    jessica_results = adapter.search("WELL-", user_id="U-202", conn=conn)
    conn.close()

    assert [result["memory"] for result in michael_results] == ["Michael discussed WELL-0121"]
    assert [result["memory"] for result in jessica_results] == ["Jessica discussed WELL-0777"]
    assert all(user_id == "U-201" for _, user_id in client.add_calls[:1] + client.search_calls[:1])
    assert all(user_id == "U-202" for _, user_id in client.add_calls[1:] + client.search_calls[1:])


def test_mem0_adapter_uses_isolated_sqlite_fallback_without_api_key(monkeypatch):
    from src.memory.mem0_adapter import Mem0Adapter

    monkeypatch.delenv("MEM0_API_KEY", raising=False)
    conn = get_connection(":memory:")
    init_db(conn)
    record_turn(
        user_id="U-201",
        conn=conn,
        query_text="Pump vibration follow-up",
        response_summary="Discussed WELL-0121 pump vibration and inspection INS-0121-001.",
        last_discussed_wells=["WELL-0121"],
    )
    record_turn(
        user_id="U-202",
        conn=conn,
        query_text="Different maintenance issue",
        response_summary="Discussed WELL-0777 flowline leak.",
        last_discussed_wells=["WELL-0777"],
    )
    adapter = Mem0Adapter()

    michael_results = adapter.search("pump vibration", user_id="U-201", conn=conn)
    jessica_results = adapter.search("pump vibration", user_id="U-202", conn=conn)

    assert any("WELL-0121" in result["memory"] for result in michael_results)
    assert jessica_results == []
    conn.close()


def test_exa_tool_executes_and_formats_external_citations(monkeypatch):
    from src.domain import exa_search

    calls = []

    class FakeExa:
        def __init__(self, api_key):
            assert api_key == "test-exa-key"

        def search_and_contents(self, query, **kwargs):
            calls.append((query, kwargs))
            return SimpleNamespace(results=[SimpleNamespace(
                title="EPA Oil Spill Reporting Guide",
                url="https://www.epa.gov/oil-spills",
                text="Operators should report qualifying discharges promptly.",
            )])

    monkeypatch.setenv("EXA_API_KEY", "test-exa-key")
    monkeypatch.setattr(exa_search, "Exa", FakeExa, raising=False)

    result = execute_tool(
        "search_external_oilfield_knowledge",
        {"query": "EPA oil spill reporting requirements"},
    )

    expected_citation = "EXA:EPA Oil Spill Reporting Guide|https://www.epa.gov/oil-spills"
    assert calls and calls[0][0] == "EPA oil spill reporting requirements"
    assert result["evidence_ids"] == [expected_citation]
    assert result["results"][0]["citation"] == f"[{expected_citation}]"
    assert result["visual"]["evidence_items"][0]["url"] == "https://www.epa.gov/oil-spills"


def test_exa_tool_falls_back_cleanly_when_offline(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)

    result = execute_tool(
        "search_external_oilfield_knowledge",
        {"query": "OSHA oilfield spill response rules"},
    )

    assert result["status"] == "offline"
    assert result["results"] == []
    assert result["evidence_ids"] == []
    assert "EXA:" not in str(result)


def test_agent_loop_routes_external_regulatory_context_to_exa(monkeypatch):
    from src.domain import exa_search
    from backend.copilot.agent.loop import AgentLoop

    class FakeExa:
        def __init__(self, api_key):
            pass

        def search_and_contents(self, query, **kwargs):
            return SimpleNamespace(results=[SimpleNamespace(
                title="OSHA Oilfield Spill Response",
                url="https://www.osha.gov/oil-gas",
                text="External safety guidance.",
            )])

    class StubLLM:
        provider = "offline"
        api_key = None

        def _route_query_to_tool(self, message):
            return None

        def chat_completion(self, messages, **kwargs):
            return {"content": "", "tool_calls": [], "model": "test"}

        def _synthesize_prose(self, tool_data):
            citations = " ".join(row["citation"] for row in tool_data.get("results", []))
            return f"External sources found. {citations}".strip()

    monkeypatch.setenv("EXA_API_KEY", "test-exa-key")
    monkeypatch.setattr(exa_search, "Exa", FakeExa, raising=False)
    conn = get_connection(":memory:")
    init_db(conn)

    result = AgentLoop(llm_client=StubLLM()).run_turn(
        "What are the external OSHA oilfield spill response requirements?",
        user_id="U-201",
        conn=conn,
    )

    conn.close()
    assert [tool["name"] for tool in result["agent_trace"]["tools_invoked"]] == [
        "search_documentation",
        "search_external_oilfield_knowledge",
    ]
    assert "[EXA:OSHA Oilfield Spill Response|https://www.osha.gov/oil-gas]" in result["content"]
    assert result["agent_trace"]["citations_verified"] is True


def test_agent_loop_syncs_user_scoped_memory_and_reports_engine():
    from backend.copilot.agent.loop import AgentLoop
    from src.memory.mem0_adapter import Mem0Adapter

    client = FakeMem0Client()

    class StubLLM:
        provider = "offline"
        api_key = None

        def __init__(self):
            self.seen_messages = []

        def _route_query_to_tool(self, message):
            return None

        def chat_completion(self, messages, **kwargs):
            self.seen_messages.append(messages)
            return {"content": "Review the telemetry evidence.", "tool_calls": [], "model": "test"}

        def _synthesize_prose(self, tool_data):
            return "No result."

    llm = StubLLM()
    agent = AgentLoop(llm_client=llm, memory_adapter=Mem0Adapter(memory=client))
    conn = get_connection(":memory:")
    init_db(conn)

    agent.run_turn("Tell me about WELL-0121 pump vibration", user_id="U-201", conn=conn)
    response = agent.run_turn("Follow up on WELL-0121", user_id="U-201", conn=conn)

    saved_users = [user_id for _, user_id in client.add_calls]
    searched_users = [user_id for _, user_id in client.search_calls]
    assert saved_users == ["U-201", "U-201"]
    assert searched_users == ["U-201", "U-201"]
    assert response["agent_trace"]["memory_engine"] == "sqlite+mem0"
    assert "Private long-term memory" in llm.seen_messages[-1][0]["content"]
    assert conn.execute("SELECT COUNT(*) FROM user_messages WHERE user_id = 'U-201'").fetchone()[0] == 2
    conn.close()
