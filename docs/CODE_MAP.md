# CODE_MAP.md — Asset Intelligence Copilot Codebase Map

## Architecture Overview

```text
[Dataset Roots: data/sample-data, ...]
       │
       ▼
[loader.py / reports.py / docs.py / rules.py]
       │
       ▼
[SQLite DB: raw tables + FTS5 doc_chunks + ledger]
       │
       ▼
[effective.py: eff_inspection, well_now, spills] ──► [resolver.py / params.py]
       │
       ▼
[downtime.py / spills.py / compliance.py]
       │
       ▼
[tools/analytics.py, tools/render.py, tools/memory_tools.py]
       │
       ▼
[agent/loop.py + guardrails.py] ◄──► [FastAPI /api/chat + SSE]
                                           │
                                           ▼
                                 [Vite + React UI]
```

## Directory & File Registry

| File / Path | Phase | Purpose | Status |
|---|---|---|---|
| `rules.yaml` | M1 | Extracted fleet & well-type thresholds with source file & section citations | Completed |
| `backend/copilot/config.py` | M1 | Environment config, AS_OF ("2026-10-17"), DATASET_ROOTS, DB paths | Completed |
| `backend/copilot/db.py` | M1 | SQLite connection, table schemas (raw, FTS5, derived, ledger), indices | Completed |
| `backend/copilot/resolver.py` | M1-M2 | Entity resolution (wells, areas, users) and relative time window math | Completed |
| `backend/copilot/ingest/rules.py` | M1 | Extractor parsing markdown manuals & SOPs into `rules.yaml` | Completed |
| `backend/copilot/ingest/reports.py` | M1 | Fast regex parser extracting structured facts from `maintenance-reports/*.md` | Completed |
| `backend/copilot/ingest/docs.py` | M1 | Markdown section chunker and SQLite FTS5 indexer for SOPs and manuals | Completed |
| `backend/copilot/ingest/loader.py` | M1 | Multi-root idempotent loader for JSON, JSONL, reports, docs into SQLite | Completed |
| `backend/copilot/domain/effective.py` | M2 | Materializes `eff_inspection`, `well_now`, and `spills` derived views/tables | Completed |
| `backend/copilot/domain/downtime.py` | M2 | Downtime calculation (7 days per non-producing inspection) and rankings | Completed |
| `backend/copilot/domain/spills.py` | M2 | Spills queries, volumetric totals, area × month heatmaps, and map coordinates | Completed |
| `backend/copilot/domain/params.py` | M3 | Scoped parameter lookup (`fleet` -> `well_type` -> `well` -> `inspection`) | Completed |
| `backend/copilot/domain/compliance.py` | M3 | Deterministic protocol checks: SR-01..03, RC-02, RC-04, RCA, shut-in rules | Completed |
| `backend/copilot/tools/analytics.py` | M2-M3 | Tool wrapper functions for domain logic queries | Completed |
| `backend/copilot/tools/render.py` | M2-M3 | Visual payload generators (StatusCard, Table, LineChart, BarChart, Map, Heatmap) | Completed |
| `src/memory/ledger.py` | M4 | Level-1 Shared Fleet Memory, append-only runtime corrections, rule overrides, and reactive diffs | Completed |
| `src/domain/claims.py` | M4 | Conflict detection engine cross-examining sensor data, inspector remarks, and notes | Completed |
| `src/memory/recall.py` | M4 | Level-2 SQL-enforced per-user private conversation and entity memory | Completed |
| `backend/copilot/memory/ledger.py` | M4 | Append-only audit ledger for corrections, feedback, and parameter overrides | Completed |
| `backend/copilot/memory/claims.py` | M4 | Conflict detection and truth dispute resolution across users & sensor data | Completed |
| `backend/copilot/memory/recall.py` | M4 | Per-user isolated conversational memory | Completed |
| `backend/copilot/tools/memory_tools.py` | M4 | Memory and feedback tool APIs for ledger, claims, and private recall | Completed |
| `backend/copilot/tools/docs_tools.py` | M5 | FTS5 documentation search tool with section citation grounding | Completed |
| `backend/copilot/tools/registry.py` | M5 | Unified tool definition registry and session-injecting dispatch engine | Completed |
| `backend/copilot/agent/llm.py` | M5 | Provider-agnostic LLM interface (Gemma 4 / Ollama / OpenAI / fallback) | Completed |
| `backend/copilot/agent/prompts.py` | M5 | System prompt enforcing zero math, evidence citation, and no invented causes | Completed |
| `backend/copilot/agent/guardrails.py` | M5 | Rule 6 citation guardrail auditing and sanitizing bracketed IDs | Completed |
| `backend/copilot/agent/loop.py` | M5 | Agentic conversation loop orchestrating tools, visual blocks, and guardrails | Completed |
| `backend/copilot/api/sse.py` | M5 | Server-Sent Events real-time event streaming helper | Completed |
| `backend/copilot/api/main.py` | M5 | FastAPI application serving `/api/chat`, `/api/users`, `/api/wells`, `/api/health` | Completed |
| `backend/tests/test_agent_and_api.py` | M5 | Pytest suite validating agent loop, guardrails, tools, and FastAPI endpoints | Completed (100% green) |
| `frontend/src/App.tsx` | M5 | Vite React main application container with sidebar & quick prompts | Completed |
| `frontend/src/Chat.tsx` | M5 | Interactive conversational thread with streaming and citation chips | Completed |
| `frontend/src/UserPicker.tsx` | M5 | User profile switcher enforcing Rule 5 server-side session identity | Completed |
| `frontend/src/blocks/*.tsx` | M5 | 8 Generative visual blocks (StatusCard, Table, LineChart, BarChart, Map, Heatmap, Conflict, Evidence) | Completed |
| `backend/tests/test_holdout.py` | M6 | Multi-root test-data rehearsal suite validating dynamic DATA_END and hot-loading | Completed (100% green) |
| `scripts/make_holdout.py` | M6 | Generator for synthetic 2-hour holdout test-data directory | Completed |
| `README.md` | M6 | Production architecture documentation, 1-command quickstart, and hot-drop instructions | Completed |
| `backend/copilot/api/main.py` (/api/admin/ingest & /api/vision/check) | M6 | Hot-drop dataset ingestion and multimodal vision cross-examination endpoints | Completed |
| `frontend/src/Chat.tsx` (Voice + Vision + Audit Drawer) | M6 | Web Speech hands-free mic, inspection photo upload, and execution trace drawer | Completed |
| `backend/tests/test_golden.py` | M1-M3 | Pytest suite validating Golden Q1–Q10 against data & compliance layers | Completed (100% green) |
| `backend/tests/test_memory.py` | M4 | Pytest suite validating Golden Q11–Q18 memory, ledger, and conflicts | Completed (100% green) |
| `backend/tests/test_scope.py` | M4 | Pytest suite validating strict scope discipline & user isolation | Completed (100% green) |
| `tests/test_m4_memory_and_claims.py` | M4 | Verification suite for Q11-Q18, user isolation, rule scope, and citation audits | Completed (100% green) |
| `tests/golden_cases.yaml` | M0 | Golden query specs, entity targets, windows, and exact expected values | Completed |


