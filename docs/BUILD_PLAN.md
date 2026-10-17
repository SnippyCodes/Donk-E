# BUILD_PLAN.md — Implementation Milestones & Roadmap

## Milestone Schedule
- [x] **M0 (15%):** Architecture, Domain Rules, Memory Spec, and `tests/golden_cases.yaml` defined.
- [ ] **M1 (35% — by 12:15 PM):** Repo scaffold, multi-root idempotent SQLite ingest (`loader.py`), report fact parser (`reports.py` >98% coverage), FTS5 doc chunker (`docs.py`), and `rules.yaml` extracted with citations.
- [ ] **M2 (55% — by 1:00 PM):** Derived tables (`eff_inspection`, `well_now`, `spills`) + fuzzy entity/window resolver + analytics functions (`downtime.py`, `spills.py`). **Golden Q1–Q8 pass at data layer**.
- [ ] **M3 (70% — by 1:45 PM):** Deterministic compliance engine (`compliance.py`: `SR-01..03`, `RC-02`, `RC-04`, `RCA`, shut-in rules) + `params.py` scoped rule resolver. **Golden Q9 & Q10 pass at data layer**.
- [ ] **M4 (85% — by 2:30 PM):** Append-only `ledger.py`, `claims.py` conflict detector, and `recall.py` per-user private memory. **Golden Q11–Q18, `test_memory.py`, and `test_scope.py` pass**.
- [ ] **M5 (95% — by 3:45 PM):** Provider-agnostic Gemma 4 agent loop (`loop.py`), citation guardrail (`guardrails.py`), FastAPI `/api/chat`, and Vite React Generative UI (all 8 visual block types + UserPicker).
- [ ] **M6 (100% — by 5:00 PM):** `scripts/make_holdout.py` multi-root rehearsal green, LLM token/latency logger active, `README.md` & `LICENSE` (MIT) pushed, DevRelay & OrganizerHQ ready.
