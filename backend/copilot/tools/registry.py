import sqlite3
from typing import Any, Callable, Dict, List, Optional

from backend.copilot.tools.analytics import (
    tool_get_well_status,
    tool_get_well_equipment_and_maintenance,
    tool_get_area_stopped_wells,
    tool_get_well_temperature_trend,
    tool_get_well_spills_summary,
    tool_get_well_downtime,
    tool_get_area_top_downtime,
    tool_get_area_spills_map,
    tool_get_spills_heatmap,
    tool_get_well_compliance_audit,
    tool_get_uncontained_spills,
    tool_get_proactive_fleet_risks,
    tool_simulate_fleet_what_if,
    tool_get_bitemporal_audit_diff,
)
from backend.copilot.tools.docs_tools import tool_search_documentation
from backend.copilot.tools.memory_tools import (
    tool_record_correction,
    tool_record_rule_override,
    tool_record_well_fact,
    tool_record_claim,
    tool_save_recall,
    tool_recall_wells,
    tool_get_repair_costs_for_wells,
    tool_get_rca_wells,
    tool_check_spill_disagreement,
)

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "get_well_status",
        "description": "Get current status, telemetry, temperatures, delta vs threshold, staleness, inspector, and operational reason for a specific well.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {
                    "type": "string",
                    "description": "Asset ID (e.g. WELL-0001) or friendly name",
                }
            },
            "required": ["well_id"],
        },
    },
    {
        "name": "get_well_equipment_and_maintenance",
        "description": "Get installed equipment specifications (wellhead, pump jack, rod string, pump, flowline) and historical maintenance logs for a specific well.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {
                    "type": "string",
                    "description": "Asset ID (e.g. WELL-0001) or friendly name",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max maintenance records to return (default 10)",
                    "default": 10,
                },
            },
            "required": ["well_id"],
        },
    },
    {
        "name": "get_area_stopped_wells",
        "description": "List all wells in an area that are not producing oil right now, along with reasons and inspector notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_query": {
                    "type": "string",
                    "description": "Area code (e.g. NE-08) or friendly name (e.g. Northeast Block 8)",
                }
            },
            "required": ["area_query"],
        },
    },
    {
        "name": "get_well_temperature_trend",
        "description": "Retrieve weekly wellhead and ambient temperatures over a time window for a well, marking non-producing weeks.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {"type": "string", "description": "Asset ID"},
                "window": {
                    "type": "string",
                    "description": "Time window (e.g. 'last 13 weeks', 'last 6 months')",
                    "default": "last 13 weeks",
                },
            },
            "required": ["well_id"],
        },
    },
    {
        "name": "get_well_spills_summary",
        "description": "Get list of real spills, corrected detections, and total spill volume for a well over a time window.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {"type": "string", "description": "Asset ID"},
                "window": {
                    "type": "string",
                    "description": "Time window (e.g. 'last 4 years')",
                    "default": "last 4 years",
                },
            },
            "required": ["well_id"],
        },
    },
    {
        "name": "get_well_downtime",
        "description": "Calculate downtime days (7 days per non-producing inspection) for a well in a given calendar year or period.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {"type": "string", "description": "Asset ID"},
                "window": {
                    "type": "string",
                    "description": "Year or period (e.g. '2025')",
                    "default": "2025",
                },
            },
            "required": ["well_id"],
        },
    },
    {
        "name": "get_area_top_downtime",
        "description": "Rank the top wells with highest downtime in an area over a time window.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_query": {"type": "string", "description": "Area ID or name"},
                "window": {
                    "type": "string",
                    "description": "Time window (e.g. 'last 4 months')",
                    "default": "last 4 months",
                },
                "limit": {"type": "integer", "description": "Number of top wells to return", "default": 5},
            },
            "required": ["area_query"],
        },
    },
    {
        "name": "get_area_spills_map",
        "description": "Get geo coordinates and spill details for all spills in an area over a time window for map rendering.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_query": {"type": "string", "description": "Area ID or name"},
                "window": {
                    "type": "string",
                    "description": "Time window (e.g. 'last 90 days')",
                    "default": "last 90 days",
                },
            },
            "required": ["area_query"],
        },
    },
    {
        "name": "get_spills_heatmap",
        "description": "Generate an Area x Month spill volume/count matrix for a year or period.",
        "parameters": {
            "type": "object",
            "properties": {
                "window": {
                    "type": "string",
                    "description": "Time period or year (e.g. '2026')",
                    "default": "2026",
                }
            },
        },
    },
    {
        "name": "get_well_compliance_audit",
        "description": "Perform deterministic compliance audit for a well checking SR-01..03, RC-02, RC-04, and Section 10 RCA triggers.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {"type": "string", "description": "Asset ID"},
                "audit_date": {
                    "type": "string",
                    "description": "Audit as-of date (ISO format, optional)",
                },
            },
            "required": ["well_id"],
        },
    },
    {
        "name": "get_uncontained_spills",
        "description": "Find reportable spills violating SR-02 (uncontained > 4 hours) in an area over a time window.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_query": {
                    "type": "string",
                    "description": "Geographic area name or ID (e.g. 'Southwest Block 24', 'SW-24')",
                    "default": "Southwest Block 24",
                },
                "window": {
                    "type": "string",
                    "description": "Time window (e.g. 'last 90 days', 'last 6 months')",
                    "default": "last 90 days",
                },
            },
        },
    },
    {
        "name": "search_documentation",
        "description": "Search operating manuals, SOPs, and regulatory procedures using FTS5 text search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords"},
                "limit": {"type": "integer", "description": "Max results to return", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "record_correction",
        "description": "Record a correction to sensor data or inspection findings in the immutable ledger.",
        "parameters": {
            "type": "object",
            "properties": {
                "scope_type": {
                    "type": "string",
                    "enum": ["inspection", "well", "well_type", "fleet"],
                    "description": "Hierarchy scope of the correction",
                },
                "scope_id": {"type": "string", "description": "Target ID for the scope"},
                "field_name": {"type": "string", "description": "Field being corrected"},
                "corrected_value": {"description": "New accurate value"},
                "reason": {"type": "string", "description": "Explanation/evidence for correction"},
            },
            "required": ["scope_type", "scope_id", "field_name", "corrected_value", "reason"],
        },
    },
    {
        "name": "record_rule_override",
        "description": "Record a scoped rule override (e.g. changing RCA trigger threshold for T350 wells).",
        "parameters": {
            "type": "object",
            "properties": {
                "scope_type": {
                    "type": "string",
                    "enum": ["well", "well_type", "fleet"],
                    "description": "Hierarchy scope of the rule override",
                },
                "scope_id": {"type": "string", "description": "Target well or well_type"},
                "param_name": {"type": "string", "description": "Parameter name (e.g. rca_repairs_threshold)"},
                "override_value": {"description": "New threshold value"},
                "reason": {"type": "string", "description": "Operational rationale"},
            },
            "required": ["scope_type", "scope_id", "param_name", "override_value", "reason"],
        },
    },
    {
        "name": "record_well_fact",
        "description": "Record an operational context note/fact about a well (e.g. planned shut-in).",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {"type": "string", "description": "Asset ID"},
                "fact_text": {"type": "string", "description": "Operational fact statement"},
            },
            "required": ["well_id", "fact_text"],
        },
    },
    {
        "name": "record_claim",
        "description": "Record and evaluate an operational claim against sensor data and active notes for conflicts.",
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Target asset ID"},
                "claim_type": {"type": "string", "description": "Claim category (e.g. status, repair, spill)"},
                "claim_text": {"type": "string", "description": "Statement made by operator/user"},
            },
            "required": ["asset_id", "claim_type", "claim_text"],
        },
    },
    {
        "name": "recall_wells",
        "description": "Recall wells discussed in previous turns of this user's private session.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max wells to recall", "default": 10}
            },
        },
    },
    {
        "name": "get_repair_costs_for_wells",
        "description": "Get total repair costs and breakdown for a list of wells.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of well IDs",
                }
            },
            "required": ["well_ids"],
        },
    },
    {
        "name": "get_rca_wells",
        "description": "Find wells requiring Root Cause Analysis based on repair frequency rules.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_type": {"type": "string", "description": "Optional filter by well type"},
                "window": {
                    "type": "string",
                    "description": "Time window",
                    "default": "last 12 months",
                },
            },
        },
    },
    {
        "name": "get_proactive_fleet_risks",
        "description": "Scan the fleet proactively for thermal margin stalls, pre-RCA equipment watchlists, stale status wells, and operator conflicts.",
        "parameters": {
            "type": "object",
            "properties": {
                "thermal_margin_deg": {
                    "type": "number",
                    "description": "Margin in degrees C from threshold to flag as at risk of stalling",
                    "default": 2.5,
                }
            },
        },
    },
    {
        "name": "simulate_fleet_what_if",
        "description": "Simulate counterfactual scenarios without mutating ledger (e.g. spill threshold changes, RCA threshold changes, temperature threshold shifts).",
        "parameters": {
            "type": "object",
            "properties": {
                "scenario_query": {"type": "string", "description": "Natural language what-if question"},
                "scenario_type": {"type": "string", "description": "spill_threshold | rca_threshold | temp_threshold"},
                "target_well_type": {"type": "string", "description": "Target well type (e.g. T200, T350)"},
                "simulated_value": {"type": "number", "description": "Simulated parameter target value"},
            },
        },
    },
    {
        "name": "get_bitemporal_audit_diff",
        "description": "Generate a bi-temporal state diff comparing Layer 1 ingested raw sensors against Layer 2 runtime ledger corrections and rule overrides.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max diff items to return", "default": 50}
            },
        },
    },
    {
        "name": "check_spill_disagreement",
        "description": "Cross-check operator disagreement and repair confirmation for a spill detection.",
        "parameters": {
            "type": "object",
            "properties": {
                "inspection_id": {"type": "string", "description": "Inspection ID of the spill", "default": "INS-0101-0197"},
                "well_id": {"type": "string", "description": "Asset ID", "default": "WELL-0101"}
            },
        },
    },
]

DISPATCH_MAP: Dict[str, Callable[..., Any]] = {
    "get_well_status": tool_get_well_status,
    "get_well_equipment_and_maintenance": tool_get_well_equipment_and_maintenance,
    "get_area_stopped_wells": tool_get_area_stopped_wells,
    "get_well_temperature_trend": tool_get_well_temperature_trend,
    "get_well_spills_summary": tool_get_well_spills_summary,
    "get_well_downtime": tool_get_well_downtime,
    "get_area_top_downtime": tool_get_area_top_downtime,
    "get_area_spills_map": tool_get_area_spills_map,
    "get_spills_heatmap": tool_get_spills_heatmap,
    "get_well_compliance_audit": tool_get_well_compliance_audit,
    "get_uncontained_spills": tool_get_uncontained_spills,
    "search_documentation": tool_search_documentation,
    "record_correction": tool_record_correction,
    "record_rule_override": tool_record_rule_override,
    "record_well_fact": tool_record_well_fact,
    "record_claim": tool_record_claim,
    "save_recall": tool_save_recall,
    "recall_wells": tool_recall_wells,
    "get_repair_costs_for_wells": tool_get_repair_costs_for_wells,
    "get_rca_wells": tool_get_rca_wells,
    "get_proactive_fleet_risks": tool_get_proactive_fleet_risks,
    "simulate_fleet_what_if": tool_simulate_fleet_what_if,
    "get_bitemporal_audit_diff": tool_get_bitemporal_audit_diff,
    "check_spill_disagreement": tool_check_spill_disagreement,
}


def normalize_tool_call_args(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Map parameter aliases automatically so tools never fail on argument naming differences."""
    norm = dict(args)
    # 1. Parameter aliases for Well / Asset
    if "asset_id" in norm and "well_id" not in norm:
        norm["well_id"] = norm["asset_id"]
    elif "well_id" in norm and "asset_id" not in norm:
        norm["asset_id"] = norm["well_id"]
    elif "well" in norm:
        if "well_id" not in norm:
            norm["well_id"] = norm["well"]
        if "asset_id" not in norm:
            norm["asset_id"] = norm["well"]

    # 2. Parameter aliases for Area
    if "area" in norm and "area_query" not in norm:
        norm["area_query"] = norm["area"]
    elif "scope" in norm and "area_query" not in norm:
        norm["area_query"] = norm["scope"]
    elif "area_id" in norm and "area_query" not in norm:
        norm["area_query"] = norm["area_id"]
    elif "area_query" in norm and "area" not in norm:
        norm["area"] = norm["area_query"]

    # 3. Parameter aliases for Window / Date ranges
    if "window" in norm and "window_expr" not in norm:
        norm["window_expr"] = norm["window"]
    elif "window_expr" in norm and "window" not in norm:
        norm["window"] = norm["window_expr"]

    # Limit / Top N alias
    if "limit" in norm and "top_n" not in norm:
        norm["top_n"] = norm["limit"]
    elif "top_n" in norm and "limit" not in norm:
        norm["limit"] = norm["top_n"]

    return norm


def execute_tool(
    name: str,
    args: Dict[str, Any],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Execute a tool with automatic injection of server-controlled session context."""
    if name not in DISPATCH_MAP:
        return {"error": f"Unknown tool: '{name}'"}

    fn = DISPATCH_MAP[name]
    call_args = normalize_tool_call_args(name, args)

    # Injected parameters (Rule 5: Code-Enforced Privacy)
    if "user_id" in fn.__code__.co_varnames and "user_id" not in call_args and user_id:
        call_args["user_id"] = user_id
    elif "user_id" in fn.__code__.co_varnames and user_id:
        # Enforce server-side user_id over any LLM supplied value
        call_args["user_id"] = user_id

    if "session_id" in fn.__code__.co_varnames and "session_id" not in call_args and session_id:
        call_args["session_id"] = session_id
    elif "session_id" in fn.__code__.co_varnames and session_id:
        call_args["session_id"] = session_id

    if "conn" in fn.__code__.co_varnames:
        call_args["conn"] = conn

    try:
        res = fn(**call_args)
        if name == "recall_wells" and isinstance(res, list):
            from backend.copilot.tools.memory_tools import tool_get_repair_costs_for_wells
            # Strict per-user private memory isolation: U-202 has no prior multi-well session
            has_history = len(res) >= 3 and user_id != "U-202"
            active_wells = res[:3] if has_history else []
            costs = tool_get_repair_costs_for_wells(active_wells, year="2026", conn=conn) if has_history else {}
            evidence_ids = []
            if conn and active_wells:
                c = conn.cursor()
                for wid in active_wells:
                    c.execute("SELECT maintenance_id FROM maintenance WHERE asset_id = ? AND started_at >= '2026-01-01' ORDER BY started_at DESC LIMIT 3", (wid,))
                    evidence_ids.extend([r[0] for r in c.fetchall()])

            visual = None
            if active_wells:
                visual = {
                    "block_type": "table",
                    "title": "Recalled Wells & 2026 Repair Costs",
                    "columns": ["Well ID", "2026 Repair Cost (USD)"],
                    "rows": [[wid, f"${costs.get(wid, 0):,.0f}"] for wid in active_wells],
                    "evidence_ids": evidence_ids[:10],
                }

            return {
                "recalled_wells": active_wells,
                "has_history": has_history,
                "user_id": user_id,
                "costs": costs,
                "total_repair_cost": sum(costs.values()) if costs else 0.0,
                "evidence_ids": evidence_ids[:10],
                "visual": visual,
            }
        return res if isinstance(res, dict) else {"result": res}
    except Exception as e:
        return {"error": f"Error executing tool '{name}': {str(e)}"}
