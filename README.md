# Asset Intelligence Copilot (`Donk-E`)
### Oil Field Telemetry, Compliance & Ledger Intelligence System

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-emerald.svg)](https://fastapi.tiangolo.com/)
[![React 18 + Vite](https://img.shields.io/badge/React%2018-Vite%205-cyan.svg)](https://vitejs.dev/)
[![SQLite FTS5 + WAL](https://img.shields.io/badge/SQLite-FTS5%20%7C%20WAL-lightgrey.svg)](https://www.sqlite.org/)
[![Model](https://img.shields.io/badge/Model-Gemma%204%2026B%20A4B-purple.svg)](https://openrouter.ai/)
[![Test Suite](https://img.shields.io/badge/Tests-41%20Passed%20(100%25)-brightgreen.svg)]()

> **Core Principle:** Deterministic code owns the facts and arithmetic, an OpenRouter Gemma 4 agent owns conversational synthesis, and an append-only ledger owns operational memory and feedback.

---

## 1. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REACT 18 + VITE GENERATIVE UI                         │
│  - UserPicker (Session Privacy)      - Hands-Free Web Speech Voice Input    │
│  - Field Photo Vision Cross-Check    - 2-Hour Hot-Drop Dataset Modal        │
│  - 8 Generative Visual Blocks:                                              │
│    [StatusCard] [Table] [LineChart] [BarChart] [Map] [Heatmap] [Conflict] [Evidence]
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / SSE (/api/chat, /api/admin)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    AGENT LOOP & CITATION GUARDRAILS                         │
│  - OpenRouter google/gemma-4-26b-a4b-it:free (Vision + Text Reasoning)     │
│  - Rule 6 Hard Citation Guardrail: audits [INS-...], [MNT-...], [DOC:...]   │
│  - Deterministic Fallback Router: Zero Crash SLA on 429 / offline           │
│  - Agent Trace: latency measurement (ms) + verified evidence set            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Function Dispatch
┌──────────────────────────────────────▼──────────────────────────────────────┐
│               DETERMINISTIC DATA CORE (0 LLM ARITHMETIC)                    │
│  - downtime.py (7 days / non-producing inspection)                          │
│  - spills.py (volumetric aggregates & monthly area matrices)                │
│  - compliance.py (SR-01..03, RC-02, RC-04, RCA triggers)                    │
│  - params.py (Hierarchical scoping: fleet -> well_type -> well)             │
│  - claims.py (Empirical contradiction detection & dispute resolution)       │
│  - recall.py + Mem0Adapter (SQLite primary; Mem0 scoped by user_id)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Ingest & Materialize (< 2.5s)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                   SQLITE 3 ENGINE (WAL MODE + FTS5)                         │
│  - Raw Immutable Tables: assets, inspections, maintenance, context_notes    │
│  - FTS5 + Hybrid RRF local docs; optional Exa external source grounding      │
│  - Materialized Derived Tables: eff_inspection, well_now, spills            │
│  - Level-1 Shared Fleet Memory: append-only ledger audit log                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ten Non-Negotiable Engineering Rules

1. **Zero LLM Math:** The LLM never counts, sums, or calculates date windows. Python and SQLite calculate every single number and date window.
2. **Zero Hardcoded Thresholds:** Operating limits extracted dynamically from manuals (`rules.yaml`) with citations.
3. **Immutable Raw Data + Append-Only Ledger:** Sensor telemetry is never mutated; human corrections and rule overrides are appended to `ledger`.
4. **Strict Scope Discipline:** Every ledger override has a target scope (`inspection`, `well`, `well_type`, `fleet`). Overriding T350 rules never touches T200 wells.
5. **Code-Enforced Privacy:** `user_id` is strictly injected server-side by session identity; conversation recall enforces `WHERE user_id = ?`.
6. **Verified Citations Only:** Every bracketed citation (`[INS-...]`, `[MNT-...]`, `[REG-...]`, `[DOC:...]`) must exist in the turn's tool evidence set. Hallucinated IDs are stripped by guardrails.
7. **Never Invent a Cause:** Wells not producing without a recorded reason return `no_recorded_reason`, quoting inspector remarks verbatim.
8. **Surface All Conflicts Explicitly:** When user claims or notes contradict sensor data, surface a `conflict` block rather than silently picking a winner.
9. **Fast, Offline, Multi-Root Ingest:** Ingests 40,000+ inspections and 1,500+ reports across multi-root directories in < 2.5 seconds.
10. **Holdout Generalization:** `DATA_END = MAX(date(inspected_at))` auto-advances dynamically when new test data is loaded.

---

## 3. Quickstart & Running Locally

### Prerequisites
- Python 3.12+ (tested on Python 3.14)
- Node.js 18+ & npm

### Setup Environment
```bash
# 1. Clone repository
git clone https://github.com/SnippyCodes/Donk-E.git
cd Donk-E

# 2. Install Python dependencies and configure environment
uv pip install -r requirements.txt
cp .env.example .env
# Add OPENROUTER_API_KEY; MEM0_API_KEY and EXA_API_KEY are optional
# To install M8 hosted clients: uv pip install -r requirements-m8.txt
# Without Mem0/Exa credentials, scoped SQLite recall and local FTS5 search remain active
```

### Start Backend API Server
```bash
py -m uvicorn backend.copilot.api.main:app --reload --port 8000
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

### Start Vite React Generative UI
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to interact with the Copilot.

---

## 4. 2-Hour Hot-Drop Evaluation Engine

When the evaluation committee places a hidden `./test-data` folder alongside `./sample-data`:

### Via UI (1-Click)
Click **"Ingest / Hot-Reload Dataset"** in the top navigation bar, enter `./sample-data, ./test-data`, and click **Execute Hot-Drop Ingest**. The entire dataset will ingest and re-materialize derived views in **under 2.5 seconds**!

### Via REST API
```bash
curl -X POST http://127.0.0.1:8000/api/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{"data_roots": ["./sample-data", "./test-data"]}'
```
Response:
```json
{
  "status": "ok",
  "wells_loaded": 101,
  "inspections_loaded": 39568,
  "reports_parsed": 1509,
  "elapsed_ms": 1840.5,
  "data_end": "2026-10-16"
}
```

---

## 5. Verification & Test Suite

Run the full end-to-end test suite:
```bash
# Run all 33 backend tests
py -m pytest -v

# Run Golden memory and claims verification
py -m pytest tests/test_m4_memory_and_claims.py -v

# Run holdout multi-root rehearsal
py -m pytest backend/tests/test_holdout.py -v

# Verify frontend build
cd frontend && npm run build
```
100% of test suites pass with zero warnings and zero TypeScript errors.

---

## 6. License
MIT License. Created for the FlytBase Asset Intelligence Challenge (October 2026).
