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
| `backend/copilot/memory/ledger.py` | M4 | Append-only audit ledger for corrections, feedback, and parameter overrides | Completed |
| `backend/copilot/memory/claims.py` | M4 | Conflict detection and truth dispute resolution across users & sensor data | Completed |
| `backend/copilot/memory/recall.py` | M4 | Per-user isolated conversational memory | Completed |
| `backend/copilot/tools/memory_tools.py` | M4 | Memory and feedback tool APIs for ledger, claims, and private recall | Completed |
| `backend/tests/test_golden.py` | M1-M3 | Pytest suite validating Golden Q1–Q10 against data & compliance layers | Completed (100% green) |
| `backend/tests/test_memory.py` | M4 | Pytest suite validating Golden Q11–Q18 memory, ledger, and conflicts | Completed (100% green) |
| `backend/tests/test_scope.py` | M4 | Pytest suite validating strict scope discipline & user isolation | Completed (100% green) |
| `tests/golden_cases.yaml` | M0 | Golden query specs, entity targets, windows, and exact expected values | Completed |
