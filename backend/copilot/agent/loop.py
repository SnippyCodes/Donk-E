import json
import sqlite3
import time
from typing import Any, Dict, List, Optional

from backend.copilot.agent.guardrails import CitationGuardrail
from backend.copilot.agent.llm import LLMClient
from backend.copilot.agent.prompts import SYSTEM_PROMPT
from backend.copilot.db import get_connection
from backend.copilot.tools.registry import TOOL_DEFINITIONS, execute_tool


class AgentLoop:
    """Provider-agnostic agent loop executing tool-calling, citation guardrails, and generative UI."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
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
            messages.append({"role": "user", "content": message})

            # LLM invocation
            llm_resp = self.llm.chat_completion(messages, tools=TOOL_DEFINITIONS)
            tool_calls = llm_resp.get("tool_calls", [])

            visual_blocks: List[Dict[str, Any]] = []
            collected_evidence: List[str] = []
            conflicts: List[Dict[str, Any]] = []
            tools_trace: List[Dict[str, Any]] = []
            raw_prose = llm_resp.get("content", "")
            target_asset_id: Optional[str] = None

            # Execute tool calls
            raw_tool_results = []
            if tool_calls:
                for tc in tool_calls:
                    fn_name = tc["name"]
                    fn_args = tc.get("args", {})
                    if "asset_id" in fn_args:
                        target_asset_id = fn_args["asset_id"]
                    elif "well_id" in fn_args:
                        target_asset_id = fn_args["well_id"]

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

                # Turn 2: Feed tool results back to LLM for conversational synthesis
                if not raw_prose and raw_tool_results:
                    if getattr(self.llm, "provider", "") in ("openrouter", "gemma", "ollama", "openai", "vllm") and getattr(self.llm, "api_key", None):
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

            # Save session recall for discussed well if present
            if target_asset_id:
                execute_tool(
                    "save_recall",
                    {
                        "key": f"last_well_{target_asset_id}",
                        "value_json": {"well_id": target_asset_id, "query": message},
                    },
                    user_id=user_id,
                    session_id=sess_id,
                    conn=conn,
                )

            total_elapsed_ms = round((time.perf_counter() - turn_start) * 1000, 2)

            agent_trace = {
                "tools_invoked": tools_trace,
                "reasoning_details": llm_resp.get("reasoning_details") or "Deterministic rule evaluation & scoped resolution",
                "citations_verified": audit_result["is_valid"],
                "grounded_ids": audit_result["valid_citations"],
                "model": llm_resp.get("model", "google/gemma-4-26b-a4b-it:free"),
                "provider": getattr(self.llm, "provider", "openrouter"),
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
                "citation_audit": {
                    "valid": audit_result["valid_citations"],
                    "stripped": audit_result["invalid_citations"],
                },
            }
        finally:
            if close_conn:
                conn.close()
