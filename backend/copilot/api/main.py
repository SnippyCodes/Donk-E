import json
import sqlite3
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.copilot.agent.loop import AgentLoop
from backend.copilot.api.sse import format_sse
from backend.copilot.resolver import get_data_end
from backend.copilot.db import get_connection
from backend.copilot.tools.registry import execute_tool


app = FastAPI(
    title="Asset Intelligence Copilot API",
    description="Deterministic operations assistant and agentic copilot for oil and gas fields.",
    version="1.0.0",
)

# Enable CORS for React frontend (Vite default is 5173, allow all local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = AgentLoop()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "U-102"  # Default: Jake Morales
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None


class FeedbackRequest(BaseModel):
    user_id: str
    scope_type: str
    scope_id: str
    field_name: str
    corrected_value: Any
    reason: str


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Health check with dynamic dataset metrics."""
    conn = get_connection()
    try:
        data_end = get_data_end(conn)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM assets")
        asset_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM inspections")
        inspection_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM ledger")
        ledger_count = c.fetchone()[0]
        return {
            "status": "ok",
            "data_end": data_end,
            "counts": {
                "assets": asset_count,
                "inspections": inspection_count,
                "ledger_entries": ledger_count,
            },
        }
    finally:
        conn.close()


@app.get("/api/users")
def get_users() -> List[Dict[str, Any]]:
    """Return list of operators, inspectors, and supervisors for the UserPicker."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT user_id, name, role, team_id FROM users ORDER BY user_id")
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()


@app.get("/api/wells")
def get_wells(limit: int = 100) -> List[Dict[str, Any]]:
    """Return wells with their latest operational status."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT w.asset_id, w.name, w.well_type, w.area_id, ar.name as area_name,
                   w.is_producing, w.recorded_status, w.wellhead_temp_c, w.ambient_temp_c,
                   w.delta_temp_c, w.reason_summary
            FROM well_now w
            JOIN areas ar ON w.area_id = ar.area_id
            ORDER BY w.asset_id
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()


@app.get("/api/insights/proactive")
def get_proactive_insights(thermal_margin: float = 2.5) -> Dict[str, Any]:
    """M7 Deliverable A: Proactive Autonomous Anomaly & Risk Radar."""
    from backend.copilot.domain.radar import scan_proactive_fleet_risks
    return scan_proactive_fleet_risks(thermal_margin_deg=thermal_margin)



@app.post("/api/chat")
def chat_turn(req: ChatRequest) -> Dict[str, Any]:
    """Process a conversational query and return grounded prose and generative visual blocks."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    res = agent.run_turn(
        message=req.message,
        user_id=req.user_id,
        session_id=req.session_id,
        history=req.history,
    )
    return res


@app.get("/api/chat/stream")
def chat_stream(
    message: str = Query(...),
    user_id: str = Query("U-102"),
    session_id: Optional[str] = Query(None),
):
    """Server-Sent Events streaming endpoint for real-time copilot responses."""
    def event_generator():
        # Yield metadata
        yield format_sse({"status": "processing", "user_id": user_id}, event="start")
        
        # Run turn
        turn_result = agent.run_turn(
            message=message,
            user_id=user_id,
            session_id=session_id,
        )

        # Stream visual blocks
        for block in turn_result.get("visual_blocks", []):
            yield format_sse(block, event="block")

        # Stream evidence
        if turn_result.get("evidence_ids"):
            yield format_sse({"evidence_ids": turn_result["evidence_ids"]}, event="evidence")

        # Stream text content
        yield format_sse({"content": turn_result["content"]}, event="content")

        # Stream completion
        yield format_sse({"status": "completed"}, event="end")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/feedback")
def submit_feedback(fb: FeedbackRequest) -> Dict[str, Any]:
    """Submit a human correction or rule override to the immutable ledger."""
    res = execute_tool(
        "record_correction",
        {
            "scope_type": fb.scope_type,
            "scope_id": fb.scope_id,
            "field_name": fb.field_name,
            "corrected_value": fb.corrected_value,
            "reason": fb.reason,
        },
        user_id=fb.user_id,
    )
    return res


@app.get("/api/ledger")
def get_ledger(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve audit history from the append-only ledger."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason
            FROM ledger
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = []
        for r in c.fetchall():
            d = dict(r)
            try:
                d["payload"] = json.loads(d["payload_json"])
            except Exception:
                d["payload"] = d["payload_json"]
            rows.append(d)
        return rows
    finally:
        conn.close()


class IngestRequest(BaseModel):
    data_roots: Optional[List[str]] = None


@app.post("/api/admin/ingest")
def admin_ingest(req: Optional[IngestRequest] = None) -> Dict[str, Any]:
    """Hot-Drop Dataset Ingestion Endpoint.
    
    Accepts arbitrary dataset roots (e.g. ["./sample-data", "./test-data"]),
    gracefully skips missing roots, idempotently re-ingests in < 2.5s,
    and recalculates dynamic DATA_END.
    """
    import time
    from pathlib import Path
    from backend.copilot.config import BASE_DIR, get_dataset_roots
    from backend.copilot.ingest.loader import load_dataset

    t0 = time.perf_counter()
    raw_roots = req.data_roots if (req and req.data_roots) else None

    if raw_roots:
        resolved_paths: List[Path] = []
        for r in raw_roots:
            p = Path(r)
            if not p.is_absolute():
                # Test multiple standard prefixes
                candidates = [BASE_DIR / p, BASE_DIR / "data" / p.name, p]
                found = next((c for c in candidates if c.exists()), None)
                if found:
                    resolved_paths.append(found)
            elif p.exists():
                resolved_paths.append(p)
        # Deduplicate
        seen = set()
        valid_paths = [p for p in resolved_paths if not (str(p) in seen or seen.add(str(p)))]
    else:
        valid_paths = get_dataset_roots()

    if not valid_paths:
        valid_paths = get_dataset_roots()

    counts = load_dataset(roots=valid_paths)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    conn = get_connection()
    try:
        data_end = get_data_end(conn)
    finally:
        conn.close()

    return {
        "status": "ok",
        "wells_loaded": counts.get("assets", 0),
        "inspections_loaded": counts.get("inspections", 0),
        "reports_parsed": counts.get("report_facts", 0),
        "elapsed_ms": elapsed_ms,
        "data_end": data_end,
        "loaded_roots": [str(p) for p in valid_paths],
    }


class VisionCheckRequest(BaseModel):
    well_id: str
    image_base64: str
    notes: Optional[str] = None
    user_id: str = "U-102"


@app.post("/api/vision/check")
def vision_check(req: VisionCheckRequest) -> Dict[str, Any]:
    """Field Operator Visual Inspection Cross-Check.
    
    Sends base64 field image to Gemma 4 26B A4B vision to extract visual observations
    and cross-examines findings against the latest recorded inspection (Rule 8).
    """
    prompt = (
        f"You are inspecting oil well {req.well_id}. "
        "Describe the operating condition: is the pump jack moving or stationary? "
        "Is there any visible oil spill, sheen, or pooled fluid on the pad? "
        "Return a concise 2-sentence field observation."
    )
    vision_res = agent.llm.analyze_image(req.image_base64, prompt)
    observation_text = vision_res.get("description", "")

    # Cross-examine against telemetry with claims engine
    claim_res = execute_tool(
        "record_claim",
        {
            "asset_id": req.well_id,
            "claim_type": "visual_inspection",
            "claim_text": f"Field Photo: {observation_text}",
        },
        user_id=req.user_id,
    )

    return {
        "well_id": req.well_id,
        "observation": observation_text,
        "model": vision_res.get("model", "gemma-4-vision"),
        "claim_verdict": claim_res.get("conflict_verdict", "recorded"),
        "conflict_details": claim_res.get("conflict_details", ""),
        "conflict_block": claim_res if claim_res.get("conflict_verdict") in ("contradicts_data", "contradicts_other_note") else None,
        "evidence_ids": claim_res.get("evidence_ids", []),
    }

