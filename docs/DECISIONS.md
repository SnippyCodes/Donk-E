# DECISIONS.md — Architectural & Engineering Decision Record

## Decision 1: Zero Hardcoded Thresholds & `rules.yaml`
- **Context:** Oil well thermal limits (T200 = 15°C, T350 = 20°C), spill classes (reportable >= 5 bbl), containment deadlines (4h), RCA triggers (3 corrective events in 12 months) must not be scattered as magic numbers.
- **Decision:** Extract every parameter from `fleet/well-types/*.md` and `fleet/sops/*.md` into `rules.yaml` with explicit citations (`param`, `value`, `unit`, `applies_to`, `source_file`, `source_section`).
- **Impact:** Dynamic parameter resolution supports holdout test datasets with new well types and runtime overrides (e.g. Q14 T350 2-repair RCA).

## Decision 2: SQLite as Local Ingestion & Analytics Engine
- **Context:** Ingestion must be fast (<30s), completely offline, idempotent, and support multi-root dataset directories.
- **Decision:** Store raw ingested records into indexed SQLite tables (`assets`, `inspections`, `maintenance`, `regulatory_events`, `context_notes`, `report_facts`) and build deterministic derived tables (`eff_inspection`, `well_now`, `spills`).
- **Impact:** Ingests 40,000+ inspections and 1,500+ reports in ~5 seconds using batch inserts. Zero external database dependencies.

## Decision 3: Deterministic Code Controls Facts & Math, LLM Handles Conversation
- **Context:** Evaluation criteria penalize arithmetic hallucination, wrong windows, and ungrounded citations.
- **Decision:** Python & SQLite compute all counts, sums, downtime days (7 days per non-producing inspection), relative dates, and compliance evaluations. LLM loop invokes domain tools and provides conversational prose citing only verified IDs from tool output.
- **Impact:** 100% mathematical consistency and verifiable audit trail.

## Decision 4: Window Math Tied to Dynamic `DATA_END`
- **Context:** Challenge dataset ends on 2026-10-16. Holdout dataset in final 2 hours may have different end dates.
- **Decision:** Compute `DATA_END = MAX(date(inspected_at))` dynamically across all loaded inspections. Resolve relative windows ("last 4 months", "last 90 days", "last 13 weeks") backward from `DATA_END` using calendar-inclusive date arithmetic.
- **Impact:** Seamless compatibility across sample and holdout datasets.

## Decision 5: Non-Destructive Corrections & Conflict Retention
- **Context:** Raw sensor data, human notes, and user statements can disagree or correct each other.
- **Decision:** Raw tables are immutable. Human context corrections override effective tables (`eff_inspection`), while disagreement (e.g., inspector "Pump jack not moving" vs thermal gun correction) is flagged and surfaced as a conflict rather than silently dropped.
- **Impact:** Transparent reasoning for operators and adherence to Rule 8.

## Decision 6: CTE-Optimized Derived Table Materialization
- **Context:** Materializing `well_now` across 40,000+ inspections with correlated subqueries caused quadratic execution latency.
- **Decision:** Replaced correlated subquery with an indexed Common Table Expression (`WITH latest AS (SELECT asset_id, MAX(inspected_at) AS max_at FROM eff_inspection GROUP BY asset_id)`) and composite indices on `(asset_id, inspected_at DESC)`.
- **Impact:** Multi-root ingestion of 39,567 inspections, 5,665 maintenance records, and 1,509 reports dropped to 2.54 seconds (under 30s SLA by >10x).

## Decision 7: Append-Only Feedback Ledger & Non-Destructive Reactive Rebuild
- **Context:** Operators correct raw inspection values, AI estimates, and rule thresholds. Rule 3 strictly forbids modifying raw tables.
- **Decision:** All user corrections, rule overrides, facts, and claims are appended to an immutable `ledger` table with `{entry_id, created_at, user_id, scope_type, scope_id, entry_type, payload_json, reason}`. Rebuilding derived tables (`eff_inspection`, `well_now`, `spills`) overlays ledger entries non-destructively atop pristine raw data, computing reactive `cascade_impact` diffs in under 0.5s.
- **Impact:** 100% adherence to Rule 3 (Immutable Raw Data), auditability, and instant rollbacks.

## Decision 8: Code-Enforced Private Conversational Memory & Conflict Detection
- **Context:** Multiple users query the copilot. Conversations must remain strictly private per-user (Rule 5), while operational facts and corrections must be visible fleet-wide (Q15, Q16). Human claims and notes frequently contradict sensor data or other users (Q12, Q17, Q18).
- **Decision:** `recall.py` strictly filters `WHERE user_id = ?` using server-injected session identity (never LLM parameters). `claims.py` checks assertions against both empirical sensor data and active notes, returning structured verdicts (`consistent`, `contradicts_data`, `contradicts_other_note`) with all conflicting citations surfaced rather than silently picking a winner.
- **Impact:** Zero cross-tenant data leakage between operators and full transparency on disputed asset states.
