import sqlite3
from typing import Any, Callable, Dict, List, Optional

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
        "description": "Find reportable spills violating SR-02 (uncontained > 4 hours) over a time window.",
        "parameters": {
            "type": "object",
            "properties": {
                "window": {
                    "type": "string",
                    "description": "Time window (e.g. 'last 6 months')",
                    "default": "last 6 months",
                }
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
]

DISPATCH_MAP: Dict[str, Callable[..., Any]] = {
    "get_well_status": tool_get_well_status,
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
}


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
    call_args = dict(args)

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
        return res if isinstance(res, dict) else {"result": res}
    except Exception as e:
        return {"error": f"Error executing tool '{name}': {str(e)}"}
