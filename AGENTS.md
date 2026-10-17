# AGENTS.md — Asset Intelligence Copilot (Master Specification & Live Tracker)

Context and execution tracker for Antigravity[cite: 5]. Read this file completely, then read `tests/golden_cases.yaml` and `docs/` before writing any code[cite: 5].

## 0. Live Build Progress Tracker (Update Checkboxes After Every Phase!)

**AGENT INSTRUCTION:** After completing each task or phase, you MUST update the checkboxes `[x]` and the **Completion Percentage** below inside `AGENTS.md`, update `docs/CODE_MAP.md` and `docs/DECISIONS.md`, and print a 5-bullet summary for the human author.

- **Current Progress:** `100% Complete | 0% Remaining` (Target Finish: **5:00 PM IST, Sat 17 Oct 2026**)[cite: 8]
- [x] **M0 (15%):** Architecture, Domain Rules, Memory Spec, and `tests/golden_cases.yaml` defined[cite: 2, 3, 6, 9].
- [x] **M1 (35% — by 12:15 PM):** Repo scaffold, multi-root idempotent SQLite ingest (`loader.py`), report fact parser (`reports.py` >98% coverage), FTS5 doc chunker (`docs.py`), and `rules.yaml` extracted with citations[cite: 3, 5, 8].
- [x] **M2 (55% — by 1:00 PM):** Derived tables (`eff_inspection`, `well_now`, `spills`) + fuzzy entity/window resolver + analytics functions (`downtime.py`, `spills.py`). **Golden Q1–Q8 pass at data layer**[cite: 3, 6, 8, 9].
- [x] **M3 (70% — by 1:45 PM):** Deterministic compliance engine (`compliance.py`: `SR-01..03`, `RC-02`, `RC-04`, `RCA`, shut-in rules) + `params.py` scoped rule resolver. **Golden Q9 & Q10 pass at data layer**[cite: 3, 6, 8, 9].
- [x] **M4 (85% — by 2:30 PM):** Append-only `ledger.py`, `claims.py` conflict detector, and `recall.py` per-user private memory. **Golden Q11–Q18, `test_memory.py`, and `test_scope.py` pass**[cite: 2, 6, 8].
- [x] **M5 (95% — by 3:45 PM):** Provider-agnostic Gemma 4 agent loop (`loop.py`), citation guardrail (`guardrails.py`), FastAPI `/api/chat`, and Vite React Generative UI (all 8 visual block types + UserPicker)[cite: 3, 5, 8].
- [x] **M6 (100% — by 5:00 PM):** `scripts/make_holdout.py` multi-root rehearsal green, LLM token/latency logger active, `README.md` & `LICENSE` (MIT) pushed, DevRelay & OrganizerHQ ready[cite: 1, 7, 8].
- [x] **M7 (Advanced Differentiators):** Proactive Anomaly Radar (`radar.py` & `/api/insights/proactive`), Counterfactual What-If Simulator (`simulator.py`), Hybrid RRF Search (`hybrid_search.py`), and Bi-Temporal Audit Diff (`diff.py`) fully verified (39/39 backend tests green).
- [x] **M8 (Mentor Bonus & Industrial Polish):** Universal argument normalization (`backend/copilot/tools/`), raw Gemma 4 `<|tool_call>` regex parser in `llm.py`, Markdown pipe table stripper in `guardrails.py`, Deterministic QA Validation Engine (`validate_turn_qa` & `GET /api/qa/golden-suite` 18/18 pass in 66ms), and strict GitHub Primer Dark / Vercel Geist monochrome UI.
- [x] **M9 (Automated End-to-End QA & Self-Healing Audit):** Full 18/18 scenarios (Q1–Q18) running sequentially through full `AgentLoop`, stateful multi-user carry-forward verified across all 4 pillars (0 LLM math, citation provenance, visual contracts, multi-user isolation), 18/18 pass in 2.44s, `GET /api/qa/audit` exposed with self-healing bug log, `docs/QA_REPORT.md` published, and `make holdout` rehearsal 100% green.

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
```

---

## 9. Automated End-to-End QA & Self-Healing Audit

### 4-Pillar End-to-End QA Contract

To guarantee absolute compliance with hackathon scoring criteria, all copilot interactions are continuously verified against a 4-pillar QA specification across both Part A (Q1–Q14) and Part B (Q15–Q18):

1. **Pillar 1: Fact & Numeric Invariant Gate (0 LLM Math)**
   - Every number, well ID, date, dollar cost, downtime day count, spill barrel volume, and status in `tests/golden_cases.yaml` (Q1–Q18) is computed strictly by Python/SQLite deterministic code.
   - The end-to-end output of `/api/chat` and `agent.loop` must contain the exact computed invariants without truncation or hallucinated arithmetic.

2. **Pillar 2: Citation Provenance Gate (Strict Set Membership)**
   - 100% of bracketed IDs in generated responses (`[INS-...]`, `[MNT-...]`, `[REG-...]`, `[CTX-...]`, `[DOC:...]`, `[RPT:...]`, `[LEDGER-...]`) must be members of the deterministic tool outputs' `evidence` set for that specific turn.
   - Post-turn sanitizer in `guardrails.py` strips or rejects ungrounded citations before transmission to the user.

3. **Pillar 3: Visual Contract Verification**
   - Asserts the exact visual block (`status_card`, `table`, `line_chart`, `bar_chart`, `map_view`, `heatmap`, `conflict`, `none`) is emitted, properly typed, and strictly matches expected row, pin, marker, and matrix counts.

4. **Pillar 4: Stateful Multi-User Carry-Forward & Scope Isolation**
   - **Q6 (Michael) -> Q11 (Michael new chat):** Michael Turner queries top downtime wells in NE-07 in Q6 (`WELL-0121, WELL-0138, WELL-0107`); in Q11, a new session correctly recalls these 3 wells and computes 2026 repair costs (`WELL-0121: $25,794, WELL-0138: $46,942, WELL-0107: $5,176`).
   - **Q16 (Jessica Private Isolation):** Jessica Reed asks about past conversations and gets zero history (`no earlier conversation` found), strictly enforcing `WHERE user_id = ?` isolation.
   - **Q12 (Michael Temperature Correction):** Michael corrects `INS-0164-0205` wellhead temp from 24.0°C to 41.0°C. System overlays ledger, flips `is_producing=true`, detects conflict with Tyler Hughes's inspector remark (`"Pump jack not moving."`), and re-evaluating Q2 removes `WELL-0164` (leaving 3 stopped wells: `WELL-0170, WELL-0172, WELL-0175`).
   - **Q15 (Jessica Sees Michael's Correction):** Jessica Reed queries `WELL-0164` and sees it producing oil (`41.0°C`), attributed to Michael Turner's correction, with the unresolved inspector conflict explicitly flagged.
   - **Q13 (Michael Spill Volume Correction):** Michael corrects `INS-0151-0201` spill volume from 4.5 to 5.4 bbl. Spill crosses the 5.0 bbl threshold to become reportable, triggering `SR-01` breach (written report overdue), invalidating `MNT-0151-025` "moderate" classification, flagging `SR-02` (6.4h > 4h limit), and scheduling `SR-03` due `2026-11-23`.
   - **Q15 (Laura Simmons Sees Reportable Spill):** Laura Simmons queries reportable spills in NE Block 8 in the last 90 days and sees `WELL-0151` (5.4 bbl).
   - **Q14 (T350 Rule Override & Scope Containment):** Michael overrides pump jack RCA threshold for `well_type = 'T350'` from 3 to 2 repairs. RCA list adds `WELL-0120` (T350, 2 repairs) alongside `WELL-0108, WELL-0121, WELL-0138`. `WELL-0102` (T200, 2 repairs) is strictly excluded due to scope containment. Rule attribution to Michael Turner is recorded.
   - **Q17 (User vs Data Conflicts):** Claims contradicting empirical data (e.g., Tyler Hughes claiming `WELL-0175` running fine when delta is 0.4°C and Michael recorded a shut-in; Jake Morales claiming `WELL-0001` back online when delta is 3.2°C) surface both sides with unverified claims marked unconfirmed.
   - **Q18 (Disputed AI Analysis):** Disagreement on whether `INS-0101-0197` at `WELL-0101` was crude oil (Chris Dalton CTX-0101-003, confirmed by repair MNT-0101-029) or produced water (Ryan Brooks CTX-0101-002) is preserved and surfaced transparently without silently dropping evidence.

