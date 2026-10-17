# ARCHITECTURE.md — Asset Intelligence Copilot Architecture

## 1. System Overview

The Asset Intelligence Copilot is an AI-powered operations assistant for oil and gas well fields. It combines deterministic data engineering (SQLite + Python domain analytics), multi-root data ingestion, full-text search (SQLite FTS5), scoped compliance verification, append-only audit ledgers, and an LLM agent with generative visual outputs.

## 2. Layered Architecture

1. **Ingestion & Indexing Layer (`backend/copilot/ingest/`):**
   - Multi-root loader (`loader.py`): Supports multiple comma-separated roots (`DATASET_ROOTS`). Loads JSON, JSONL, free-text markdown reports, and documentation manuals.
   - Report Fact Parser (`reports.py`): High-speed regex extraction of containment times, repair protocols, pressure tests, waste manifests, and RCA escalation flags from `maintenance-reports/*.md`.
   - FTS5 Document Chunker (`docs.py`): Parses SOPs and manuals into searchable semantic chunks (`doc_chunks`) with section-level citations.
   - Rule Extractor (`rules.py`): Extracts operating thresholds and SOP limits into `rules.yaml`.

2. **Derived Data & Window Resolution Layer (`backend/copilot/domain/`, `resolver.py`):**
   - `eff_inspection`: Joins inspections with well metadata and applies human context corrections (`context_notes`) to produce effective temperatures, production state (`is_producing`), and validated spill detections.
   - `well_now`: Computes the latest status of each well, detects staleness against `recorded_status`, and determines operational reasons (open repairs, planned shut-ins, or `no_recorded_reason`).
   - `spills`: Curates non-corrected spills with coordinates, volume, pad area %, containment hours, and reportable flags.
   - `resolver.py`: Fuzzy matching for assets, areas, and users; calendar-inclusive relative window resolution anchored to `DATA_END = MAX(date(inspected_at))`.

3. **Deterministic Analytics & Compliance Engine (`backend/copilot/domain/`):**
   - `downtime.py`: Computes downtime (7 days per non-producing inspection) and ranks assets.
   - `spills.py`: Computes volumetric aggregates, area-by-month matrices, and geospatial coordinates.
   - `compliance.py`: Deterministic rule enforcement for SR-01 (reporting deadlines), SR-02 (4-hour containment), SR-03 (60-day remediation), RC-02 (annual flowline test), RC-04 (30-day NOV response), and Section 10 RCA triggers.
   - `params.py`: Hierarchical parameter resolution with scoped overrides (`fleet` -> `well_type` -> `well` -> `inspection`).

4. **Memory, Conflict & Ledger Layer (`backend/copilot/memory/`):**
   - `ledger.py`: Append-only transaction log recording human feedback, corrections, and rule changes.
   - `claims.py`: Detects conflicting claims across users, inspector notes, and raw sensor readings.
   - `recall.py`: Enforces private per-user conversation recall (`WHERE user_id = ?`).

5. **Presentation & Generative UI Layer (`backend/copilot/tools/`, `frontend/`):**
   - Visual payload generation for 8 block types: StatusCard, Table, LineChart, BarChart, MapView, Heatmap, Conflict, and Evidence.
   - Provider-agnostic agent loop with citation guardrails.
