import json
import os
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional

from src.domain.exa_search import is_external_oilfield_query
from src.memory.mem0_adapter import Mem0Adapter

from backend.copilot.agent.guardrails import CitationGuardrail
from backend.copilot.agent.llm import LLMClient
from backend.copilot.agent.prompts import SYSTEM_PROMPT
from backend.copilot.db import get_connection
from backend.copilot.tools.registry import TOOL_DEFINITIONS, execute_tool


class AgentLoop:
    """Provider-agnostic agent loop executing tool-calling, citation guardrails, and generative UI."""

    def __init__(self, llm_client: Optional[LLMClient] = None, memory_adapter: Optional[Mem0Adapter] = None):
        self.llm = llm_client or LLMClient()
        self.memory_adapter = memory_adapter or Mem0Adapter()
        self.guardrail = CitationGuardrail(strip_invalid=True)

    def run_turn(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Execute a full conversational turn with deterministic grounding and guardrails."""
        turn_start = time.perf_counter()
        close_conn = False
        if conn is None:
            conn = get_connection()
            close_conn = True

        sess_id = session_id or f"sess_{user_id}"

        try:
            # Build conversation history
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if history:
                messages.extend(history)
            memory_results = self.memory_adapter.search(message, user_id=user_id, conn=conn, limit=5)
            if memory_results:
                memory_lines = [str(item.get("memory", "")).strip() for item in memory_results]
                memory_summary = "\n".join(line for line in memory_lines if line)[:2400]
                if memory_summary:
                    messages[0]["content"] += (
                        "\n\nPrivate long-term memory for this user (continuity hints only; "
                        "verify operational claims against current deterministic tool evidence):\n"
                        + memory_summary
                    )
            messages.append({"role": "user", "content": message})

            # External regulatory/industry context is explicitly routed to Exa.
            if is_external_oilfield_query(message):
                deterministic_call = {
                    "name": "search_external_oilfield_knowledge",
                    "args": {"query": message, "limit": 5},
                }
            else:
                # Fast-path deterministic route check (Rule 1 & Rule 2: Zero LLM Math)
                deterministic_call = self.llm._route_query_to_tool(message)
            if deterministic_call:
                if deterministic_call.get("name") == "search_external_oilfield_knowledge":
                    tool_calls = [
                        {"id": "det_call_local_docs", "name": "search_documentation", "args": {"query": message}},
                        {"id": "det_call_external", **deterministic_call},
                    ]
                else:
                    tool_calls = [{"id": "det_call_0", **deterministic_call}]
                llm_resp = {"content": "", "tool_calls": tool_calls, "model": "deterministic-router"}
            else:
                # LLM invocation for conversational queries
                llm_resp = self.llm.chat_completion(messages, tools=TOOL_DEFINITIONS)
                tool_calls = llm_resp.get("tool_calls", [])

            visual_blocks: List[Dict[str, Any]] = []
            collected_evidence: List[str] = []
            conflicts: List[Dict[str, Any]] = []
            tools_trace: List[Dict[str, Any]] = []
            raw_prose = llm_resp.get("content", "")

            # Execute tool calls
            raw_tool_results = []
            if tool_calls:
                for tc in tool_calls:
                    fn_name = tc["name"]
                    fn_args = tc.get("args", {})
                    if fn_name == "get_area_spills_map" and "reportable" in message.lower():
                        fn_args["reportable_only"] = True

                    t_tool = time.perf_counter()
                    tool_res = execute_tool(
                        fn_name,
                        fn_args,
                        user_id=user_id,
                        session_id=sess_id,
                        conn=conn,
                    )
                    elapsed_tool_ms = round((time.perf_counter() - t_tool) * 1000, 2)
                    raw_tool_results.append(tool_res)

                    # Collect visual block
                    if "visual" in tool_res and isinstance(tool_res["visual"], dict):
                        visual_blocks.append(tool_res["visual"])

                    # Collect evidence IDs
                    ev_ids = tool_res.get("evidence_ids", [])
                    if isinstance(ev_ids, list):
                        collected_evidence.extend(ev_ids)

                    # Collect conflict blocks
                    if tool_res.get("conflict_verdict") in ("contradicts_data", "contradicts_other_note"):
                        conflicts.append(tool_res)

                    # Record execution trace
                    tools_trace.append({
                        "name": fn_name,
                        "args": fn_args,
                        "elapsed_ms": elapsed_tool_ms,
                        "evidence_count": len(ev_ids) if isinstance(ev_ids, list) else 0,
                    })

                # Turn 2: Deterministic fact synthesis or conversational LLM synthesis
                if not raw_prose and raw_tool_results:
                    if deterministic_call:
                        if deterministic_call.get("name") == "search_external_oilfield_knowledge":
                            local_result: Dict[str, Any] = {}
                            external_result: Dict[str, Any] = {}
                            for called_tool, result in zip(tool_calls, raw_tool_results):
                                if called_tool.get("name") == "search_documentation":
                                    local_result = result
                                elif called_tool.get("name") == "search_external_oilfield_knowledge":
                                    external_result = result
                            local_citations = [
                                f"[{evidence_id}]"
                                for evidence_id in local_result.get("evidence_ids", [])
                                if str(evidence_id).startswith("DOC:")
                            ]
                            exa_citations = [
                                row.get("citation", "")
                                for row in external_result.get("results", [])
                                if row.get("citation")
                            ]
                            prose_parts = []
                            if local_citations:
                                prose_parts.append("Related local procedure references are also shown: " + " ".join(local_citations))
                            if exa_citations:
                                prose_parts.append(
                                    "External references returned by Exa are shown below; verify their applicability to local procedures. "
                                    + " ".join(exa_citations)
                                )
                            elif local_citations:
                                prose_parts.append("External web search is unavailable; use the cited local procedure references below.")
                            else:
                                prose_parts.append("External web search is unavailable right now. I found no external sources to cite; local SQLite manuals and SOP search remains available.")
                            raw_prose = " ".join(prose_parts)
                        else:
                            # Deterministic synthesis guarantees 0 LLM math and strict citation grounding (Rule 1 & Rule 6)
                            raw_prose = self.llm._synthesize_prose(raw_tool_results[0])
                    elif getattr(self.llm, "provider", "") in ("openrouter", "gemma", "ollama", "openai", "vllm") and getattr(self.llm, "api_key", None):
                        try:
                            turn2_messages = list(messages)
                            turn2_messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": tc.get("id", f"call_{i}"),
                                        "type": "function",
                                        "function": {
                                            "name": tc["name"],
                                            "arguments": json.dumps(tc.get("args", {})),
                                        },
                                    }
                                    for i, tc in enumerate(tool_calls)
                                ],
                            })
                            for i, (tc, tr) in enumerate(zip(tool_calls, raw_tool_results)):
                                # Filter out heavy visual payload to keep prompt fast and token-efficient
                                clean_tr = {k: v for k, v in tr.items() if k != "visual"}
                                turn2_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tc.get("id", f"call_{i}"),
                                    "name": tc["name"],
                                    "content": json.dumps(clean_tr),
                                })

                            turn2_resp = self.llm.chat_completion(turn2_messages, temperature=0.0, timeout=6.0)
                            if turn2_resp.get("content"):
                                raw_prose = turn2_resp["content"]
                                if turn2_resp.get("reasoning_details"):
                                    llm_resp["reasoning_details"] = turn2_resp["reasoning_details"]
                        except Exception:
                            raw_prose = ""

                    # Fallback synthesis if Turn 2 did not produce text
                    if not raw_prose:
                        raw_prose = self.llm._synthesize_prose(raw_tool_results[0])

            # Deduplicate evidence
            collected_evidence = list(dict.fromkeys(collected_evidence))

            # Audit and sanitize citations
            audit_result = self.guardrail.audit(raw_prose, set(collected_evidence))
            final_prose = audit_result["cleaned_text"]

            # Eliminate duplicate Markdown pipe tables when structured visual blocks are rendered
            has_structured_visual = any(
                b.get("block_type") in ("table", "bar_chart", "line_chart", "map", "map_view", "heatmap", "status_card")
                for b in visual_blocks
            )
            if has_structured_visual:
                from backend.copilot.agent.guardrails import strip_markdown_tables
                final_prose = strip_markdown_tables(final_prose)

            # Mentor Bonus: Live Deterministic QA Validation Pipeline
            from backend.copilot.agent.guardrails import validate_turn_qa
            qa_report = validate_turn_qa(
                question=message,
                tool_calls=tool_calls,
                tool_outputs=raw_tool_results,
                final_text=final_prose,
                blocks=visual_blocks,
                user_id=user_id,
                conn=conn,
            )

            # Synchronously persist this user's turn and discussed wells in SQLite first.
            memory_source = message + "\n" + final_prose + "\n" + json.dumps(raw_tool_results, default=str)
            discussed_wells = list(dict.fromkeys(re.findall(r"\bWELL-\d{4}\b", memory_source, flags=re.IGNORECASE)))
            discussed_wells = [well.upper() for well in discussed_wells]
            from src.memory.recall import record_turn
            record_turn(
                user_id=user_id,
                conn=conn,
                session_id=sess_id,
                query_text=message,
                response_summary=final_prose[:2000],
                last_discussed_wells=discussed_wells,
            )
            self.memory_adapter.add(
                [
                    {"role": "user", "content": message},
                    {
                        "role": "assistant",
                        "content": final_prose + ("\nDiscussed wells: " + ", ".join(discussed_wells) if discussed_wells else ""),
                    },
                ],
                user_id=user_id,
            )

            total_elapsed_ms = round((time.perf_counter() - turn_start) * 1000, 2)
            exa_search_succeeded = any(
                tool.get("name") == "search_external_oilfield_knowledge" and result.get("status") == "ok"
                for tool, result in zip(tools_trace, raw_tool_results)
            )

            agent_trace = {
                "tools_invoked": tools_trace,
                "reasoning_details": llm_resp.get("reasoning_details") or "Deterministic rule evaluation & scoped resolution",
                "citations_verified": audit_result["is_valid"],
                "grounded_ids": audit_result["valid_citations"],
                "model": llm_resp.get("model", "google/gemma-4-26b-a4b-it:free"),
                "provider": getattr(self.llm, "provider", "openrouter"),
                "memory_engine": self.memory_adapter.engine_name,
                "semantic_memories_used": len(memory_results),
                "search_engine": "sqlite_fts5+exa" if exa_search_succeeded else "sqlite_fts5",
                "exa_configured": bool(os.getenv("EXA_API_KEY") and not os.getenv("EXA_API_KEY", "").lower().startswith("your_")),
                "total_latency_ms": total_elapsed_ms,
            }

            return {
                "content": final_prose,
                "visual_blocks": visual_blocks,
                "evidence_ids": collected_evidence,
                "conflicts": conflicts,
                "user_id": user_id,
                "session_id": sess_id,
                "agent_trace": agent_trace,
                "qa_report": qa_report,
                "citation_audit": {
                    "valid": audit_result["valid_citations"],
                    "stripped": audit_result["invalid_citations"],
                },
            }
        finally:
            if close_conn:
                conn.close()
