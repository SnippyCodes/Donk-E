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
