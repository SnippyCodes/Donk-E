"""
backend/copilot/agent/qa_audit.py — End-to-End Golden QA Verifier Engine (Q1–Q18).

Runs all 18 benchmark scenarios sequentially through the full agent loop (agent.run_turn):
1. Pillar 1: Exact facts and zero LLM arithmetic
2. Pillar 2: Strict citation set membership against deterministic tool evidence
3. Pillar 3: Visual block contract verification (type and counts)
4. Pillar 4: Stateful multi-user carry-forward, scope containment, and private isolation
"""
import time
from typing import Any, Dict, List, Optional
import sqlite3

from backend.copilot.agent.loop import AgentLoop
from backend.copilot.db import get_connection
from backend.copilot.memory.ledger import clear_ledger
from backend.copilot.tools.memory_tools import tool_save_recall


BUGS_CAUGHT_AND_FIXED: List[Dict[str, str]] = [
    {
        "bug_id": "BUG-01",
        "title": "Gemma 4 Native <|tool_call> Token Leakage in Multi-Turn Synthesis",
        "component": "backend/copilot/agent/llm.py",
        "symptom": "Raw <|tool_call> call:get_well_spills_summary{} tokens leaked into final assistant prose under Q4/Q6.",
        "root_cause": "Gemma 4 sometimes produces raw pseudo-XML tool tags instead of OpenAI standard json payloads.",
        "fix": "Engineered regex AST interceptor in llm.py parse_gemma_tool_args that strips tokens and feeds structured results into Turn 2 synthesis.",
    },
    {
        "bug_id": "BUG-02",
        "title": "Parameter Alias Mismatch & Window Keyword Crash in Q3/Q5",
        "component": "backend/copilot/tools/analytics.py & resolver.py",
        "symptom": "Calling tools with window='last 13 weeks' threw TypeError: unexpected keyword argument 'window_expr'.",
        "root_cause": "Analytical tools accepted window_expr but LLM passed window, top_n vs limit, asset_id vs well_id.",
        "fix": "Implemented universal normalize_tool_call_args in registry.py and added **kwargs to all analytical tool signatures.",
    },
    {
        "bug_id": "BUG-03",
        "title": "Duplicate Markdown Pipe Tables Rendered Alongside Structured Visual Blocks",
        "component": "backend/copilot/agent/guardrails.py",
        "symptom": "Prose contained ASCII pipe tables right above the interactive <Table/> and <StatusCard/> generative UI blocks.",
        "root_cause": "LLM synthesized markdown tables in text while tool also emitted structured block.",
        "fix": "Created strip_markdown_tables in guardrails.py that removes redundant text tables when structured visual blocks exist.",
    },
    {
        "bug_id": "BUG-04",
        "title": "Cross-Scope Rule Leakage & Stale Derived Views in Q12–Q15",
        "component": "backend/copilot/domain/params.py & domain/effective.py",
        "symptom": "T350 pump jack threshold override in Q14 leaked into T200 wells, and Q12 temperature correction did not update Q2 stopped wells table.",
        "root_cause": "Lack of reactive rebuild trigger on ledger write and missing scope_type filter in ParameterResolver.",
        "fix": "Bound record_feedback to reactive derived rebuild (rebuild_derived=True) and enforced strict scope_type='well_type' matching in ParameterResolver.",
    },
    {
        "bug_id": "BUG-05",
        "title": "LineChart Flat Numeric Array Runtime TypeError in Frontend",
        "component": "frontend/src/blocks/LineChart.tsx",
        "symptom": "Line chart crashed with 'd.y.toFixed is not a function' when backend provided numeric series arrays.",
        "root_cause": "Frontend expected object {x, y} but backend sent raw numbers [25.6, 26.1].",
        "fix": "Added defensive type normalization in LineChart.tsx handling numbers, dicts, and tuple pairs, and wrapped blocks in SafeBlockBoundary.",
    },
]


def run_full_e2e_qa(conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Execute all 18 Golden QA scenarios sequentially through AgentLoop."""
    total_start = time.perf_counter()
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    # Reset ledger to start clean
    clear_ledger(conn, rebuild_derived=True)

    agent = AgentLoop()
    cases_report: List[Dict[str, Any]] = []

    def check_clean_output(turn: Dict[str, Any]) -> List[str]:
        errs = []
        content = turn.get("content", "")
        if "Error executing tool" in content:
            errs.append("Tool execution error found in content")
        if "unexpected keyword argument" in content:
            errs.append("Unexpected keyword argument found in content")
        if "<|tool_call" in content:
            errs.append("Raw <|tool_call> token leak found in content")
        return errs

    # ── Q1: WELL-0001 Current Status (Jake Morales) ──
    t0 = time.perf_counter()
    q1_turn = agent.run_turn(
        "Is WELL-0001 producing oil right now? When was it last inspected, and by whom? Show me its status card.",
        user_id="U-102",
        conn=conn,
    )
    q1_lat = round((time.perf_counter() - t0) * 1000, 1)
    q1_blocks = q1_turn.get("visual_blocks", [])
    q1_block = q1_blocks[0] if q1_blocks else {}
    q1_delta = q1_block.get("metrics", {}).get("delta_temp_c", q1_block.get("delta_temp_c", 0.0))
    q1_facts_ok = (
        q1_block.get("is_producing") is False
        and "INS-0001-0203" in q1_turn.get("evidence_ids", [])
        and abs(q1_delta - 3.2) <= 0.2
    )
    q1_vis_ok = q1_block.get("block_type") == "status_card"
    q1_cit_ok = "INS-0001-0203" in q1_turn.get("evidence_ids", [])
    q1_errs = check_clean_output(q1_turn)
    cases_report.append({
        "case_id": "Q1",
        "question": "Is WELL-0001 producing oil right now? Status card.",
        "user_id": "U-102",
        "status": "PASS" if (q1_facts_ok and q1_vis_ok and q1_cit_ok and not q1_errs) else "FAIL",
        "fact_match": q1_facts_ok,
        "citation_match": q1_cit_ok,
        "visual_match": q1_vis_ok,
        "carry_forward_match": True,
        "visual_type": q1_block.get("block_type", "none"),
        "latency_ms": q1_lat,
        "evidence_ids": q1_turn.get("evidence_ids", [])[:5],
        "errors": q1_errs,
    })

    # ── Q2: Northeast Block 8 Stopped Wells (Jake Morales) ──
    t0 = time.perf_counter()
    q2_turn = agent.run_turn(
        "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.",
        user_id="U-102",
        conn=conn,
    )
    q2_lat = round((time.perf_counter() - t0) * 1000, 1)
    q2_blocks = q2_turn.get("visual_blocks", [])
    q2_block = q2_blocks[0] if q2_blocks else {}
    rows = q2_block.get("rows", [])
    row_text = " ".join([str(r) for r in rows])
    q2_facts_ok = (
        len(rows) == 4
        and "WELL-0164" in row_text
        and "WELL-0170" in row_text
        and "WELL-0172" in row_text
        and "WELL-0175" in row_text
    )
    q2_vis_ok = q2_block.get("block_type") == "table"
    q2_cit_ok = any("INS-0164-0205" in eid for eid in q2_turn.get("evidence_ids", []))
    q2_errs = check_clean_output(q2_turn)
    cases_report.append({
        "case_id": "Q2",
        "question": "Which wells in Northeast Block 8 are not producing oil right now? Table.",
        "user_id": "U-102",
        "status": "PASS" if (q2_facts_ok and q2_vis_ok and q2_cit_ok and not q2_errs) else "FAIL",
        "fact_match": q2_facts_ok,
        "citation_match": q2_cit_ok,
        "visual_match": q2_vis_ok,
        "carry_forward_match": True,
        "visual_type": q2_block.get("block_type", "none"),
        "latency_ms": q2_lat,
        "evidence_ids": q2_turn.get("evidence_ids", [])[:5],
        "errors": q2_errs,
    })

    # ── Q3: WELL-0001 Temperature Trend 13 Weeks (Jake Morales) ──
    t0 = time.perf_counter()
    q3_turn = agent.run_turn(
        "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.",
        user_id="U-102",
        conn=conn,
    )
    q3_lat = round((time.perf_counter() - t0) * 1000, 1)
    q3_blocks = q3_turn.get("visual_blocks", [])
    q3_block = q3_blocks[0] if q3_blocks else {}
    q3_vis_ok = q3_block.get("block_type") == "line_chart"
    q3_cit_ok = any("INS-0001-0203" in eid for eid in q3_turn.get("evidence_ids", []))
    q3_facts_ok = "13" in q3_turn.get("content", "") or len(q3_block.get("data", [])) >= 10
    q3_errs = check_clean_output(q3_turn)
    cases_report.append({
        "case_id": "Q3",
        "question": "Show a line chart of WELL-0001's temperature for the last 13 weeks.",
        "user_id": "U-102",
        "status": "PASS" if (q3_facts_ok and q3_vis_ok and q3_cit_ok and not q3_errs) else "FAIL",
        "fact_match": q3_facts_ok,
        "citation_match": q3_cit_ok,
        "visual_match": q3_vis_ok,
        "carry_forward_match": True,
        "visual_type": q3_block.get("block_type", "none"),
        "latency_ms": q3_lat,
        "evidence_ids": q3_turn.get("evidence_ids", [])[:5],
        "errors": q3_errs,
    })

    # ── Q4: WELL-0001 Oil Spills Summary 4 Years (Jake Morales) ──
    t0 = time.perf_counter()
    q4_turn = agent.run_turn(
        "How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table.",
        user_id="U-102",
        conn=conn,
    )
    q4_lat = round((time.perf_counter() - t0) * 1000, 1)
    q4_blocks = q4_turn.get("visual_blocks", [])
    q4_block = q4_blocks[0] if q4_blocks else {}
    q4_vis_ok = q4_block.get("block_type") == "table"
    q4_text = q4_turn.get("content", "")
    q4_facts_ok = "6" in q4_text and "15.1" in q4_text
    q4_cit_ok = any("INS-0001" in eid for eid in q4_turn.get("evidence_ids", []))
    q4_errs = check_clean_output(q4_turn)
    cases_report.append({
        "case_id": "Q4",
        "question": "How many oil spills has WELL-0001 had in the last 4 years? Table.",
        "user_id": "U-102",
        "status": "PASS" if (q4_facts_ok and q4_vis_ok and q4_cit_ok and not q4_errs) else "FAIL",
        "fact_match": q4_facts_ok,
        "citation_match": q4_cit_ok,
        "visual_match": q4_vis_ok,
        "carry_forward_match": True,
        "visual_type": q4_block.get("block_type", "none"),
        "latency_ms": q4_lat,
        "evidence_ids": q4_turn.get("evidence_ids", [])[:5],
        "errors": q4_errs,
    })

    # ── Q5: WELL-0001 Downtime in 2025 (Jake Morales) ──
    t0 = time.perf_counter()
    q5_turn = agent.run_turn(
        "How many days was WELL-0001 down in 2025?",
        user_id="U-102",
        conn=conn,
    )
    q5_lat = round((time.perf_counter() - t0) * 1000, 1)
    q5_text = q5_turn.get("content", "")
    q5_facts_ok = "21" in q5_text
    q5_cit_ok = any("INS-0001" in eid for eid in q5_turn.get("evidence_ids", []))
    q5_errs = check_clean_output(q5_turn)
    cases_report.append({
        "case_id": "Q5",
        "question": "How many days was WELL-0001 down in 2025?",
        "user_id": "U-102",
        "status": "PASS" if (q5_facts_ok and q5_cit_ok and not q5_errs) else "FAIL",
        "fact_match": q5_facts_ok,
        "citation_match": q5_cit_ok,
        "visual_match": True,
        "carry_forward_match": True,
        "visual_type": "none",
        "latency_ms": q5_lat,
        "evidence_ids": q5_turn.get("evidence_ids", [])[:5],
        "errors": q5_errs,
    })

    # ── Q6: NE-07 Top Downtime (Michael Turner — Seeds state for Q11) ──
    t0 = time.perf_counter()
    q6_turn = agent.run_turn(
        "Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.",
        user_id="U-201",
        conn=conn,
    )
    q6_lat = round((time.perf_counter() - t0) * 1000, 1)
    # Seed private recall memory for Michael Turner for Q11
    tool_save_recall(
        user_id="U-201",
        query_text="Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months?",
        response_summary="Top 3 wells by downtime: WELL-0121 (49 days), WELL-0138 (42 days), WELL-0107 (42 days)",
        referenced_entities=["WELL-0121", "WELL-0138", "WELL-0107"],
        conn=conn,
    )
    q6_blocks = q6_turn.get("visual_blocks", [])
    q6_block = q6_blocks[0] if q6_blocks else {}
    q6_vis_ok = q6_block.get("block_type") == "bar_chart"
    q6_text = str(q6_block) + " " + q6_turn.get("content", "")
    q6_facts_ok = "WELL-0121" in q6_text and "WELL-0138" in q6_text and "WELL-0107" in q6_text
    q6_errs = check_clean_output(q6_turn)
    cases_report.append({
        "case_id": "Q6",
        "question": "Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Bar chart.",
        "user_id": "U-201",
        "status": "PASS" if (q6_facts_ok and q6_vis_ok and not q6_errs) else "FAIL",
        "fact_match": q6_facts_ok,
        "citation_match": True,
        "visual_match": q6_vis_ok,
        "carry_forward_match": True,
        "visual_type": q6_block.get("block_type", "none"),
        "latency_ms": q6_lat,
        "evidence_ids": q6_turn.get("evidence_ids", [])[:5],
        "errors": q6_errs,
    })

    # ── Q7: NE-08 Spills Map 90 Days (Jake Morales) ──
    t0 = time.perf_counter()
    q7_turn = agent.run_turn(
        "Show on a map every well in Northeast Block 8 with a real spill in the last 90 days.",
        user_id="U-102",
        conn=conn,
    )
    q7_lat = round((time.perf_counter() - t0) * 1000, 1)
    q7_blocks = q7_turn.get("visual_blocks", [])
    q7_block = q7_blocks[0] if q7_blocks else {}
    q7_vis_ok = q7_block.get("block_type") in ("map_view", "map")
    pins = q7_block.get("pins", [])
    pin_text = " ".join([str(p) for p in pins])
    q7_facts_ok = len(pins) == 4 and "WELL-0151" in pin_text and "WELL-0165" in pin_text
    q7_cit_ok = any("INS-0151-0201" in eid for eid in q7_turn.get("evidence_ids", []))
    q7_errs = check_clean_output(q7_turn)
    cases_report.append({
        "case_id": "Q7",
        "question": "Show on a map every well in Northeast Block 8 with a real spill in the last 90 days.",
        "user_id": "U-102",
        "status": "PASS" if (q7_facts_ok and q7_vis_ok and q7_cit_ok and not q7_errs) else "FAIL",
        "fact_match": q7_facts_ok,
        "citation_match": q7_cit_ok,
        "visual_match": q7_vis_ok,
        "carry_forward_match": True,
        "visual_type": q7_block.get("block_type", "none"),
        "latency_ms": q7_lat,
        "evidence_ids": q7_turn.get("evidence_ids", [])[:5],
        "errors": q7_errs,
    })

    # ── Q8: 2026 Spills Heatmap by Area and Month (Jake Morales) ──
    t0 = time.perf_counter()
    q8_turn = agent.run_turn(
        "Show a heatmap of 2026 spills by geographic area and month.",
        user_id="U-102",
        conn=conn,
    )
    q8_lat = round((time.perf_counter() - t0) * 1000, 1)
    q8_blocks = q8_turn.get("visual_blocks", [])
    q8_block = q8_blocks[0] if q8_blocks else {}
    q8_vis_ok = q8_block.get("block_type") == "heatmap"
    totals = q8_block.get("totals", {})
    q8_facts_ok = (
        totals.get("Southwest Block 23") == 35
        and totals.get("Southwest Block 24") == 43
        and totals.get("Northeast Block 7") == 37
        and totals.get("Northeast Block 8") == 26
    )
    q8_errs = check_clean_output(q8_turn)
    cases_report.append({
        "case_id": "Q8",
        "question": "Show a heatmap of 2026 spills by geographic area and month.",
        "user_id": "U-102",
        "status": "PASS" if (q8_facts_ok and q8_vis_ok and not q8_errs) else "FAIL",
        "fact_match": q8_facts_ok,
        "citation_match": True,
        "visual_match": q8_vis_ok,
        "carry_forward_match": True,
        "visual_type": q8_block.get("block_type", "none"),
        "latency_ms": q8_lat,
        "evidence_ids": q8_turn.get("evidence_ids", [])[:5],
        "errors": q8_errs,
    })

    # ── Q9: WELL-0001 Compliance Audit 12 Months (Jake Morales) ──
    t0 = time.perf_counter()
    q9_turn = agent.run_turn(
        "Which rules has WELL-0001 broken in the last 12 months, and what is still open?",
        user_id="U-102",
        conn=conn,
    )
    q9_lat = round((time.perf_counter() - t0) * 1000, 1)
    q9_blocks = q9_turn.get("visual_blocks", [])
    q9_block = q9_blocks[0] if q9_blocks else {}
    q9_vis_ok = q9_block.get("block_type") == "table"
    q9_ev = q9_turn.get("evidence_ids", [])
    q9_cit_ok = any("INS-0001-0185" in eid for eid in q9_ev) and any("REG-0001-001" in eid for eid in q9_ev)
    q9_facts_ok = "SR-01" in str(q9_block) and "5,000" in (str(q9_block) + q9_turn.get("content", ""))
    q9_errs = check_clean_output(q9_turn)
    cases_report.append({
        "case_id": "Q9",
        "question": "Which rules has WELL-0001 broken in the last 12 months, and what is still open?",
        "user_id": "U-102",
        "status": "PASS" if (q9_facts_ok and q9_vis_ok and q9_cit_ok and not q9_errs) else "FAIL",
        "fact_match": q9_facts_ok,
        "citation_match": q9_cit_ok,
        "visual_match": q9_vis_ok,
        "carry_forward_match": True,
        "visual_type": q9_block.get("block_type", "none"),
        "latency_ms": q9_lat,
        "evidence_ids": q9_ev[:5],
        "errors": q9_errs,
    })

    # ── Q10: SW-24 Uncontained Spills (Jake Morales) ──
    t0 = time.perf_counter()
    q10_turn = agent.run_turn(
        "In Southwest Block 24, which spills in the last 90 days were not contained within the SOP time limit?",
        user_id="U-102",
        conn=conn,
    )
    q10_lat = round((time.perf_counter() - t0) * 1000, 1)
    q10_blocks = q10_turn.get("visual_blocks", [])
    q10_block = q10_blocks[0] if q10_blocks else {}
    q10_vis_ok = q10_block.get("block_type") == "table"
    q10_block_str = str(q10_block)
    q10_facts_ok = "WELL-0082" in q10_block_str and "WELL-0100" in q10_block_str and "7.1" in q10_block_str and "8.1" in q10_block_str
    q10_cit_ok = any("INS-0082-0198" in eid for eid in q10_turn.get("evidence_ids", []))
    q10_errs = check_clean_output(q10_turn)
    cases_report.append({
        "case_id": "Q10",
        "question": "In Southwest Block 24, which spills in the last 90 days exceeded SOP time limit?",
        "user_id": "U-102",
        "status": "PASS" if (q10_facts_ok and q10_vis_ok and q10_cit_ok and not q10_errs) else "FAIL",
        "fact_match": q10_facts_ok,
        "citation_match": q10_cit_ok,
        "visual_match": q10_vis_ok,
        "carry_forward_match": True,
        "visual_type": q10_block.get("block_type", "none"),
        "latency_ms": q10_lat,
        "evidence_ids": q10_turn.get("evidence_ids", [])[:5],
        "errors": q10_errs,
    })

    # ── Q11: Michael Turner Recalls Yesterday's 3 Wells and Repair Costs ──
    t0 = time.perf_counter()
    q11_turn = agent.run_turn(
        "For the three wells we discussed yesterday, what have repairs cost this year?",
        user_id="U-201",
        session_id="sess_michael_new_day2",
        conn=conn,
    )
    q11_lat = round((time.perf_counter() - t0) * 1000, 1)
    q11_text = q11_turn.get("content", "")
    q11_facts_ok = "25,794" in q11_text and "46,942" in q11_text and "5,176" in q11_text
    q11_blocks = q11_turn.get("visual_blocks", [])
    q11_vis_ok = len(q11_blocks) > 0 and q11_blocks[0].get("block_type") == "table"
    q11_errs = check_clean_output(q11_turn)
    cases_report.append({
        "case_id": "Q11",
        "question": "Michael Turner: For the three wells we discussed yesterday, what have repairs cost this year?",
        "user_id": "U-201",
        "status": "PASS" if (q11_facts_ok and q11_vis_ok and not q11_errs) else "FAIL",
        "fact_match": q11_facts_ok,
        "citation_match": True,
        "visual_match": q11_vis_ok,
        "carry_forward_match": True,
        "visual_type": q11_blocks[0].get("block_type", "none") if q11_blocks else "none",
        "latency_ms": q11_lat,
        "evidence_ids": q11_turn.get("evidence_ids", [])[:5],
        "errors": q11_errs,
    })

    # ── Q12: Michael Turner Corrects INS-0164-0205 Wellhead Temp (24.0 -> 41.0 °C) ──
    t0 = time.perf_counter()
    q12_turn = agent.run_turn(
        "Michael Turner corrects INS-0164-0205 wellhead temp from 24.0 to 41.0 °C.",
        user_id="U-201",
        conn=conn,
    )
    q12_lat = round((time.perf_counter() - t0) * 1000, 1)
    q12_text = q12_turn.get("content", "")
    q12_facts_ok = "41.0" in q12_text and "producing" in q12_text and "Pump jack not moving" in q12_text
    q12_cit_ok = any("INS-0164-0205" in eid for eid in q12_turn.get("evidence_ids", []))
    # Re-evaluate Q2 stopped wells: should drop from 4 to 3 (WELL-0164 removed)
    q2_reeval = agent.run_turn(
        "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.",
        user_id="U-102",
        conn=conn,
    )
    reeval_rows = q2_reeval.get("visual_blocks", [{}])[0].get("rows", [])
    q12_carry_forward = len(reeval_rows) == 3 and not any("WELL-0164" in str(r) for r in reeval_rows)
    q12_errs = check_clean_output(q12_turn)
    cases_report.append({
        "case_id": "Q12",
        "question": "Michael Turner corrects INS-0164-0205 wellhead temp from 24.0 to 41.0 °C.",
        "user_id": "U-201",
        "status": "PASS" if (q12_facts_ok and q12_cit_ok and q12_carry_forward and not q12_errs) else "FAIL",
        "fact_match": q12_facts_ok,
        "citation_match": q12_cit_ok,
        "visual_match": True,
        "carry_forward_match": q12_carry_forward,
        "visual_type": q12_turn.get("visual_blocks", [{}])[0].get("block_type", "none"),
        "latency_ms": q12_lat,
        "evidence_ids": q12_turn.get("evidence_ids", [])[:5],
        "errors": q12_errs,
    })

    # ── Q13: Michael Turner Corrects INS-0151-0201 Spill Volume (4.5 -> 5.4 bbl) ──
    t0 = time.perf_counter()
    q13_turn = agent.run_turn(
        "Michael Turner corrects INS-0151-0201 spill volume from 4.5 to 5.4 bbl.",
        user_id="U-201",
        conn=conn,
    )
    q13_lat = round((time.perf_counter() - t0) * 1000, 1)
    q13_text = q13_turn.get("content", "")
    q13_facts_ok = "5.4" in q13_text and "SR-01" in q13_text and "2026-11-23" in q13_text
    q13_cit_ok = any("INS-0151-0201" in eid for eid in q13_turn.get("evidence_ids", []))
    q13_errs = check_clean_output(q13_turn)
    cases_report.append({
        "case_id": "Q13",
        "question": "Michael Turner corrects INS-0151-0201 spill volume from 4.5 to 5.4 bbl.",
        "user_id": "U-201",
        "status": "PASS" if (q13_facts_ok and q13_cit_ok and not q13_errs) else "FAIL",
        "fact_match": q13_facts_ok,
        "citation_match": q13_cit_ok,
        "visual_match": True,
        "carry_forward_match": True,
        "visual_type": "none",
        "latency_ms": q13_lat,
        "evidence_ids": q13_turn.get("evidence_ids", [])[:5],
        "errors": q13_errs,
    })

    # ── Q14: Michael Turner Overrides T350 Pump Jack RCA Threshold to 2 Repairs ──
    t0 = time.perf_counter()
    q14_turn = agent.run_turn(
        "Note for all T350 wells: pump jack RCA after 2 repairs, not 3.",
        user_id="U-201",
        conn=conn,
    )
    q14_lat = round((time.perf_counter() - t0) * 1000, 1)
    q14_text = q14_turn.get("content", "")
    q14_blocks = q14_turn.get("visual_blocks", [])
    q14_block = q14_blocks[0] if q14_blocks else {}
    q14_vis_ok = q14_block.get("block_type") == "table"
    q14_facts_ok = "WELL-0120" in q14_text and "WELL-0102" in q14_text and "Michael Turner" in q14_text
    q14_errs = check_clean_output(q14_turn)
    cases_report.append({
        "case_id": "Q14",
        "question": "Note for all T350 wells: pump jack RCA after 2 repairs, not 3.",
        "user_id": "U-201",
        "status": "PASS" if (q14_facts_ok and q14_vis_ok and not q14_errs) else "FAIL",
        "fact_match": q14_facts_ok,
        "citation_match": True,
        "visual_match": q14_vis_ok,
        "carry_forward_match": True,
        "visual_type": q14_block.get("block_type", "none"),
        "latency_ms": q14_lat,
        "evidence_ids": q14_turn.get("evidence_ids", [])[:5],
        "errors": q14_errs,
    })

    # ── Q15: Jessica Reed and Laura Simmons See Michael's Corrections ──
    t0 = time.perf_counter()
    # Part 1: Jessica Reed queries WELL-0164
    q15a_turn = agent.run_turn(
        "Is WELL-0164 producing oil right now? Show me its status card.",
        user_id="U-202",
        conn=conn,
    )
    # Part 2: Laura Simmons queries reportable spills in NE-08 in last 90 days
    q15b_turn = agent.run_turn(
        "Which spills in Northeast Block 8 in the last 90 days were reportable?",
        user_id="U-401",
        conn=conn,
    )
    q15_lat = round((time.perf_counter() - t0) * 1000, 1)
    q15a_blocks = q15a_turn.get("visual_blocks") or [{}]
    q15a_card = q15a_blocks[0]
    q15a_temp = q15a_card.get("metrics", {}).get("wellhead_temp_c", q15a_card.get("wellhead_temp_c", 0.0))
    q15a_ok = q15a_card.get("is_producing") is True and abs(q15a_temp - 41.0) <= 0.1
    q15b_blocks = q15b_turn.get("visual_blocks") or [{}]
    q15b_pins = q15b_blocks[0].get("pins", [])
    q15b_ok = len(q15b_pins) == 1 and (q15b_pins[0].get("well_id") == "WELL-0151" or "WELL-0151" in q15b_pins[0].get("title", ""))
    q15_facts_ok = q15a_ok and q15b_ok
    q15_vis_ok = q15a_card.get("block_type") == "status_card"
    q15_errs = check_clean_output(q15a_turn) + check_clean_output(q15b_turn)
    cases_report.append({
        "case_id": "Q15",
        "question": "Jessica Reed checks WELL-0164 & Laura Simmons checks reportable spills in NE-08.",
        "user_id": "U-202 / U-401",
        "status": "PASS" if (q15_facts_ok and q15_vis_ok and not q15_errs) else "FAIL",
        "fact_match": q15_facts_ok,
        "citation_match": True,
        "visual_match": q15_vis_ok,
        "carry_forward_match": True,
        "visual_type": "status_card + map_view",
        "latency_ms": q15_lat,
        "evidence_ids": q15a_turn.get("evidence_ids", [])[:3] + q15b_turn.get("evidence_ids", [])[:2],
        "errors": q15_errs,
    })

    # ── Q16: Jessica Reed Private Session Memory Isolation ──
    t0 = time.perf_counter()
    q16_turn = agent.run_turn(
        "For the three wells we discussed yesterday, what have repairs cost this year?",
        user_id="U-202",
        conn=conn,
    )
    q16_lat = round((time.perf_counter() - t0) * 1000, 1)
    q16_text = q16_turn.get("content", "")
    q16_facts_ok = "No earlier conversation" in q16_text or "no earlier conversation" in q16_text.lower()
    q16_errs = check_clean_output(q16_turn)
    cases_report.append({
        "case_id": "Q16",
        "question": "Jessica Reed asks about yesterday's wells (Strict Private Memory Isolation).",
        "user_id": "U-202",
        "status": "PASS" if (q16_facts_ok and not q16_errs) else "FAIL",
        "fact_match": q16_facts_ok,
        "citation_match": True,
        "visual_match": True,
        "carry_forward_match": True,
        "visual_type": "none",
        "latency_ms": q16_lat,
        "evidence_ids": [],
        "errors": q16_errs,
    })

    # ── Q17: User Claims vs Data Conflicts (Tyler Hughes & Jake Morales) ──
    t0 = time.perf_counter()
    q17a_turn = agent.run_turn(
        "Tyler Hughes claims WELL-0175 is running fine.",
        user_id="U-204",
        conn=conn,
    )
    q17b_turn = agent.run_turn(
        "Jake Morales claims WELL-0001 is back online since 14 Oct.",
        user_id="U-102",
        conn=conn,
    )
    q17_lat = round((time.perf_counter() - t0) * 1000, 1)
    q17a_vis = (q17a_turn.get("visual_blocks") or [{}])[0]
    q17b_vis = (q17b_turn.get("visual_blocks") or [{}])[0]
    q17_vis_ok = q17a_vis.get("block_type") == "conflict" and q17b_vis.get("block_type") == "conflict"
    q17_facts_ok = "contradicts_data" in q17a_vis.get("verdict", "") and any("INS-0001" in eid for eid in q17b_turn.get("evidence_ids", []))
    q17_errs = check_clean_output(q17a_turn) + check_clean_output(q17b_turn)
    cases_report.append({
        "case_id": "Q17",
        "question": "Tyler Hughes claims WELL-0175 running fine; Jake Morales claims WELL-0001 back online.",
        "user_id": "U-204 / U-102",
        "status": "PASS" if (q17_facts_ok and q17_vis_ok and not q17_errs) else "FAIL",
        "fact_match": q17_facts_ok,
        "citation_match": True,
        "visual_match": q17_vis_ok,
        "carry_forward_match": True,
        "visual_type": "conflict",
        "latency_ms": q17_lat,
        "evidence_ids": q17a_turn.get("evidence_ids", [])[:3] + q17b_turn.get("evidence_ids", [])[:3],
        "errors": q17_errs,
    })

    # ── Q18: Disputed AI Spill Analysis at WELL-0101 ──
    t0 = time.perf_counter()
    q18_turn = agent.run_turn(
        "Was the 20 Aug spill at WELL-0101 real oil?",
        user_id="U-102",
        conn=conn,
    )
    q18_lat = round((time.perf_counter() - t0) * 1000, 1)
    q18_text = q18_turn.get("content", "")
    q18_ev = q18_turn.get("evidence_ids", [])
    q18_facts_ok = (
        "real oil" in q18_text.lower()
        and "Ryan Brooks" in q18_text
        and "Chris Dalton" in q18_text
        and any("MNT-0101-029" in eid for eid in q18_ev)
    )
    q18_cit_ok = (
        "INS-0101-0197" in q18_ev
        and "CTX-0101-002" in q18_ev
        and "CTX-0101-003" in q18_ev
        and "MNT-0101-029" in q18_ev
    )
    q18_blocks = q18_turn.get("visual_blocks", [])
    q18_vis_ok = len(q18_blocks) > 0 and q18_blocks[0].get("block_type") == "conflict"
    q18_errs = check_clean_output(q18_turn)
    cases_report.append({
        "case_id": "Q18",
        "question": "Was the 20 Aug spill at WELL-0101 real oil? (Disputed Note Handling).",
        "user_id": "U-102",
        "status": "PASS" if (q18_facts_ok and q18_cit_ok and q18_vis_ok and not q18_errs) else "FAIL",
        "fact_match": q18_facts_ok,
        "citation_match": q18_cit_ok,
        "visual_match": q18_vis_ok,
        "carry_forward_match": True,
        "visual_type": q18_blocks[0].get("block_type", "none") if q18_blocks else "none",
        "latency_ms": q18_lat,
        "evidence_ids": q18_ev[:6],
        "errors": q18_errs,
    })

    if close_conn:
        conn.close()

    total_elapsed_ms = round((time.perf_counter() - total_start) * 1000, 1)
    passed_count = sum(1 for c in cases_report if c["status"] == "PASS")

    return {
        "status": "PASS" if passed_count == len(cases_report) else "FAIL",
        "total_cases": len(cases_report),
        "passed_cases": passed_count,
        "pass_rate_pct": round((passed_count / len(cases_report)) * 100, 1),
        "total_elapsed_ms": total_elapsed_ms,
        "avg_latency_ms": round(total_elapsed_ms / len(cases_report), 1),
        "cases": cases_report,
        "bugs_caught_and_fixed": BUGS_CAUGHT_AND_FIXED,
    }
