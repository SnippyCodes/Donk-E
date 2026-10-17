# EXPLAIN_IT.md — High-Level Architecture for Evaluators

## What is Asset Intelligence Copilot?
An agentic AI system for oilfield operations that grounds every answer in verifiable evidence from telemetry, repair reports, regulatory filings, and operational manuals.

## Core Architectural Pillars
1. **Deterministic Data Core:** Python and SQLite own all arithmetic, date comparisons, and compliance evaluations.
2. **Generative UI:** Generates fitting UI blocks (StatusCard, Table, LineChart, BarChart, MapView, Heatmap) tailored to operator queries.
3. **Evidence-Grounded Citations:** All claims are backed by structured references (`[INS-...]`, `[MNT-...]`, `[REG-...]`, `[CTX-...]`, `[DOC:...]`).
4. **Scoped Audit Ledger:** Non-destructive corrections and hierarchical rule overrides with conflict preservation.
