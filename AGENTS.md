# AGENTS.md — Asset Intelligence Copilot (Master Specification & Live Tracker)

Context and execution tracker for Antigravity[cite: 5]. Read this file completely, then read `tests/golden_cases.yaml` and `docs/` before writing any code[cite: 5].

## 0. Live Build Progress Tracker (Update Checkboxes After Every Phase!)

**AGENT INSTRUCTION:** After completing each task or phase, you MUST update the checkboxes `[x]` and the **Completion Percentage** below inside `AGENTS.md`, update `docs/CODE_MAP.md` and `docs/DECISIONS.md`, and print a 5-bullet summary for the human author.

- **Current Progress:** `85% Complete | 15% Remaining` (Target Finish: **5:00 PM IST, Sat 17 Oct 2026**)[cite: 8]
- [x] **M0 (15%):** Architecture, Domain Rules, Memory Spec, and `tests/golden_cases.yaml` defined[cite: 2, 3, 6, 9].
- [x] **M1 (35% — by 12:15 PM):** Repo scaffold, multi-root idempotent SQLite ingest (`loader.py`), report fact parser (`reports.py` >98% coverage), FTS5 doc chunker (`docs.py`), and `rules.yaml` extracted with citations[cite: 3, 5, 8].
- [x] **M2 (55% — by 1:00 PM):** Derived tables (`eff_inspection`, `well_now`, `spills`) + fuzzy entity/window resolver + analytics functions (`downtime.py`, `spills.py`). **Golden Q1–Q8 pass at data layer**[cite: 3, 6, 8, 9].
- [x] **M3 (70% — by 1:45 PM):** Deterministic compliance engine (`compliance.py`: `SR-01..03`, `RC-02`, `RC-04`, `RCA`, shut-in rules) + `params.py` scoped rule resolver. **Golden Q9 & Q10 pass at data layer**[cite: 3, 6, 8, 9].
- [x] **M4 (85% — by 2:30 PM):** Append-only `ledger.py`, `claims.py` conflict detector, and `recall.py` per-user private memory. **Golden Q11–Q18, `test_memory.py`, and `test_scope.py` pass**[cite: 2, 6, 8].
- [ ] **M5 (95% — by 3:45 PM):** Provider-agnostic Gemma 4 agent loop (`loop.py`), citation guardrail (`guardrails.py`), FastAPI `/api/chat`, and Vite React Generative UI (all 8 visual block types + UserPicker)[cite: 3, 5, 8].
- [ ] **M6 (100% — by 5:00 PM):** `scripts/make_holdout.py` multi-root rehearsal green, LLM token/latency logger active, `README.md` & `LICENSE` (MIT) pushed, DevRelay & OrganizerHQ ready[cite: 1, 7, 8].

---

## 1. Mission & Core Architecture

Build an **Asset Intelligence Copilot** that answers operators' plain-English questions about oil wells ("nodding donkeys") using weekly inspections, maintenance records, free-text repair reports, regulator events, human context notes, well-type manuals, and SOPs[cite: 1, 5, 9].

- **Core Principle:** **Deterministic code owns the facts, an LLM agent owns the conversation, and an append-only ledger owns memory and feedback**.
- **Reference Dates:** `AS_OF = "2026-10-17"` (configurable via env var)[cite: 5, 9]. `DATA_END` is computed dynamically as `MAX(date(inspected_at))` across loaded inspections (`2026-10-16` on sample data; auto-advances if the final 2-hour test dataset has newer dates)[cite: 1, 5, 9].
- **Window Resolution (`config.resolve_window`):** All timestamps are UTC; date comparisons are calendar-date inclusive on both ends[cite: 6, 9]. Relative windows are calculated backward from `DATA_END` (e.g., on sample data, `"last 4 months"` = `2026-06-16` to `2026-10-16`, `"last 90 days"` = `2026-07-19` to `2026-10-16`, `"last 13 weeks"` = `2026-07-23` to `2026-10-15`)[cite: 6, 8, 9].
- **Priority Order:** (1) Exact facts, (2) Cited evidence IDs, (3) Fitting inline visual, (4) UI polish[cite: 5, 8].

---

## 2. Ten Non-Negotiable Engineering Rules

1. **Zero LLM Math:** The LLM never counts, sums, or computes date windows[cite: 3, 5]. Python/SQLite computes every number[cite: 3, 5].
2. **Zero Hardcoded Thresholds:** Extract all thresholds/deadlines from `fleet/well-types/*.md` and `fleet/sops/*.md` into `rules.yaml` with `{param, value, unit, applies_to, source_file, source_section}`[cite: 5, 9]. If a well type has no manual/rules, return `unknown` ("no rules for type X")[cite: 3, 5, 9].
3. **Immutable Raw Data + Append-Only Ledger:** Never mutate raw tables[cite: 3, 5]. All dataset `correction` notes and runtime user feedback go into `ledger`.
4. **Strict Scope Discipline:** Every `ledger` entry has `scope_type` (`inspection | well | well_type | fleet`) and `scope_id`[cite: 2, 5]. A `T350` rule override must never affect a `T200` well (Q14).
5. **Code-Enforced Privacy:** `user_id` is injected by the server from the active UI user picker session—never passed by the LLM[cite: 2, 4, 5]. Private recall queries strictly enforce `WHERE user_id = ?` (Q11 vs Q16).
6. **Verified Citations Only:** Every bracketed ID in the assistant's prose (`[INS-...]`, `[MNT-...]`, `[REG-...]`, `[CTX-...]`, `[LEDGER-...]`, `[DOC:...]`, `[RPT:...]`) must exist in the current turn's tool `evidence` set; `guardrails.py` strips or flags anything else[cite: 3, 5, 9].
7. **Never Invent a Cause:** When a well is not producing oil and has no open repair or active note explaining why (e.g., `WELL-0164` and `WELL-0175` in Q2), return `no_recorded_reason`, surface any inspector remark (`"Pump jack not moving."`), and suggest a field check.
8. **Surface All Conflicts Explicitly:** Never silently pick a winner when a user contradicts inspection data, an inspector note contradicts a temperature correction (Q12), a user contradicts another user (Q17), or two operator notes disagree on a spill (Q18)[cite: 1, 2, 6].
9. **Fast, Offline, Multi-Root Ingest:** `DATASET_ROOTS` accepts comma-separated paths (e.g., `data/sample-data,data/test-data`)[cite: 3, 5, 8]. Ingest must be idempotent, use zero LLM calls, and finish in < 30 seconds[cite: 3, 5].
10. **Holdout Generalization:** Do not hardcode for Q1–Q18. Verify multi-root hot-loading with `make holdout`[cite: 5, 8].

---

## 3. Repository Layout & Stack

```text
AGENTS.md  README.md  LICENSE  Makefile  .env.example  rules.yaml
backend/copilot/
  config.py  db.py  resolver.py
  ingest/      loader.py  reports.py  docs.py  rules.py
  domain/      effective.py  downtime.py  spills.py  compliance.py  params.py
  memory/      ledger.py  claims.py  recall.py
  tools/       registry.py  analytics.py  docs_tools.py  memory_tools.py  render.py
  agent/       loop.py  prompts.py  llm.py  guardrails.py
  api/         main.py  sse.py
backend/tests/ test_golden.py  test_memory.py  test_scope.py  test_holdout.py
frontend/src/  App.tsx  Chat.tsx  UserPicker.tsx  blocks/{StatusCard,Table,LineChart,BarChart,MapView,Heatmap,Conflict,Evidence}.tsx
scripts/       make_holdout.py
docs/          ARCHITECTURE.md  DOMAIN_RULES.md  MEMORY_AND_FEEDBACK.md  BUILD_PLAN.md  EXPLAIN_IT.md  SUBMISSION.md  CODE_MAP.md  DECISIONS.md
tests/         golden_cases.yaml
data/          (git-ignored clone of [https://github.com/FlytBaseAILabs/flytbase-ahc-swe-asset-intelligence-dataset](https://github.com/FlytBaseAILabs/flytbase-ahc-swe-asset-intelligence-dataset))
```
