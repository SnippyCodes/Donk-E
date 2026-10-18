# MEMORY_AND_FEEDBACK.md — Two-Level Memory & Scoped Feedback Specification

## 1. Two-Level Memory System

### Shared Knowledge (Asset-Level)
- Operational facts shared by field operators, inspectors, or supervisors become visible across all users.
- Examples: Planned shut-ins (e.g. Jake Morales on WELL-0007), sensor corrections, workover schedules.
- Injected as context notes into SQLite `context_notes` and append-only `ledger`.

### Private Memory (User-Level)
- Conversational history and previous turn context belong strictly to the individual user session.
- Query isolation rule: `SELECT ... FROM user_history WHERE user_id = ?`.
- User ID is derived strictly from server-side session authentication / UI user picker; the LLM is never allowed to inject or alter user identity.

## 2. Scoped Feedback & Truth Precedence

When users provide corrections or custom rules, they are tagged with explicit hierarchical scopes:
1. `inspection`: Overrides single sensor reading or detection (e.g. WELL-0164 thermal gun correction).
2. `well`: Overrides operating status or parameters on a specific well.
3. `well_type`: Overrides parameters across all wells of that equipment class (e.g. Q14 T350 2-repair RCA override).
4. `fleet`: Overrides global defaults.

## 3. Disagreement & Conflict Resolution (Rule 8)
- Never silently discard contradicting information.
- If an inspector notes "Pump jack not moving" but a user submits a 41.0°C wellhead correction, surface both items in a `Conflict` block and prompt for supervisor confirmation.

## 4. Optional Mem0 Semantic Memory (M10 / requested M8)
- SQLite `user_sessions` and `user_messages` remain the synchronous primary store for recent turns and discussed `WELL-XXXX` IDs.
- The AgentLoop writes to SQLite first, then best-effort syncs the conversation and discussed wells to Mem0 using `memory.add(messages, user_id=<server-injected-id>)`.
- Retrieval always uses `memory.search(query, user_id=<server-injected-id>)`; results tagged with a different user are discarded. Local SQLite recall is fused with Mem0 results and remains available when the key, package, or service is unavailable.
- Never trust a memory as current operational truth. It is a continuity hint and must be checked against current deterministic evidence before making an operational claim.
- `MEM0_API_KEY` is optional and belongs only in `.env`; use a placeholder in `.env.example`.

## 5. Optional Exa External Search (M10 / requested M8)
- Use `search_external_oilfield_knowledge` for explicit external EPA/OSHA spill rules, API RP 11L standards, or industry benchmarks.
- Keep local fleet manuals and maintenance reports on SQLite FTS5 + Hybrid RRF as the primary search engine.
- Cite each external source as `[EXA:title|url]` and include its evidence ID in the current turn's evidence set. The UI validates HTTP(S) URLs before rendering clickable links.
- Without a configured `EXA_API_KEY` or when the network fails, return no external result/citation and retain local search availability.
- Keep all credentials out of source control; `.env.example` contains placeholders only.
