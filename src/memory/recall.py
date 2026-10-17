"""
src/memory/recall.py — SQL-Enforced Per-User Private Session & Entity Memory (Milestone M4)

Level-2 Private Per-User Conversational Memory in SQLite.
Enforces Rule 5 (Code-Enforced Privacy):
  - Every function requires user_id as a mandatory parameter.
  - Every query strictly enforces `WHERE user_id = ?` at the SQL layer.
  - Michael Turner's conversation history cannot be accessed by Jessica Reed,
    while both users have access to Level-1 shared fleet facts (Q11 vs Q16).
"""
import datetime
import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional


def record_turn(
    user_id: str,
    conn: sqlite3.Connection,
    session_id: Optional[str] = None,
    query_text: str = "",
    response_summary: str = "",
    last_discussed_wells: Optional[List[str]] = None,
    session_date: Optional[str] = None,
) -> str:
    """
    Record a single conversational turn in user's private session memory.

    Args:
        user_id: Mandatory user identity (server-injected, never from LLM)
        conn: Active SQLite connection
        session_id: Optional existing session ID (generated if not provided)
        query_text: The operator's prompt
        response_summary: Assistant's response summary
        last_discussed_wells: List of WELL-XXXX IDs referenced in this turn
        session_date: Optional date string (defaults to today's UTC date)

    Returns:
        The turn_id of the recorded message.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat().replace("+00:00", "Z")
    s_date = session_date or now.strftime("%Y-%m-%d")
    s_id = session_id or f"SESS-{user_id}-{uuid.uuid4().hex[:8]}"
    turn_id = f"TURN-{uuid.uuid4().hex[:10]}"

    wells = last_discussed_wells or []
    wells_json = json.dumps(wells)

    with conn:
        # Ensure session exists
        conn.execute("""
            INSERT OR IGNORE INTO user_sessions (session_id, user_id, session_date, created_at)
            VALUES (?, ?, ?, ?)
        """, (s_id, user_id, s_date, now_iso))

        # Insert private turn
        conn.execute("""
            INSERT INTO user_messages (
                turn_id, session_id, user_id, query_text, response_summary,
                last_discussed_wells_json, session_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (turn_id, s_id, user_id, query_text, response_summary, wells_json, s_date, now_iso))

        # Also insert into user_recall table for backwards compatibility
        recall_id = f"RECALL-{turn_id}"
        conn.execute("""
            INSERT INTO user_recall (entry_id, user_id, timestamp, query_text, response_summary, referenced_entities_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (recall_id, user_id, now_iso, query_text, response_summary, wells_json))

    return turn_id


def get_recent_wells(
    user_id: str,
    conn: sqlite3.Connection,
    limit: int = 10,
    lookback_days: int = 7,
) -> List[str]:
    """
    Retrieve unique well IDs discussed recently by THIS user.
    Strictly enforces `WHERE user_id = ?`.
    """
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)).isoformat().replace("+00:00", "Z")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT last_discussed_wells_json
        FROM user_messages
        WHERE user_id = ?
          AND created_at >= ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, cutoff, limit))

    wells: List[str] = []
    seen = set()
    for row in cursor.fetchall():
        w_list = json.loads(row[0] or "[]")
        for w in w_list:
            if w not in seen:
                wells.append(w)
                seen.add(w)

    return wells


def resolve_referent_wells(
    user_id: str,
    conn: sqlite3.Connection,
    query_text: str = "",
    default_count: int = 3,
) -> List[str]:
    """
    Resolve phrases like 'the three wells we discussed yesterday/earlier' (Q11, Q16).

    Args:
        user_id: The calling user
        conn: Active SQLite connection
        query_text: The operator query (optional parsing context)
        default_count: How many referent wells to resolve

    Returns:
        List of resolved well IDs. Returns [] if the user has no history.
    """
    recent = get_recent_wells(user_id, conn, limit=default_count * 2)
    return recent[:default_count]


def get_user_history(
    user_id: str,
    conn: sqlite3.Connection,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Get conversational history strictly isolated for user_id.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT turn_id, session_id, user_id, query_text, response_summary,
               last_discussed_wells_json, session_date, created_at
        FROM user_messages
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))

    history = []
    for r in cursor.fetchall():
        history.append({
            "turn_id": r["turn_id"],
            "session_id": r["session_id"],
            "user_id": r["user_id"],
            "query_text": r["query_text"],
            "response_summary": r["response_summary"],
            "last_discussed_wells": json.loads(r["last_discussed_wells_json"] or "[]"),
            "session_date": r["session_date"],
            "created_at": r["created_at"],
        })
    return history


def has_conversation_history(
    user_id: str,
    conn: sqlite3.Connection,
    lookback_days: int = 7,
) -> bool:
    """Check if user_id has any recorded conversation history."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)).isoformat().replace("+00:00", "Z")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM user_messages
        WHERE user_id = ? AND created_at >= ?
    """, (user_id, cutoff))
    cnt = cursor.fetchone()[0]
    return cnt > 0


# Backwards compatibility wrappers
def save_interaction(conn: sqlite3.Connection, user_id: str, query_text: str, response_summary: str, referenced_entities: Optional[List[str]] = None) -> str:
    return record_turn(user_id=user_id, conn=conn, query_text=query_text, response_summary=response_summary, last_discussed_wells=referenced_entities)

def recall_wells(conn: sqlite3.Connection, user_id: str, lookback_days: int = 7) -> List[str]:
    return get_recent_wells(user_id=user_id, conn=conn, lookback_days=lookback_days)

def recall_entities(conn: sqlite3.Connection, user_id: str, lookback_days: int = 7, entity_type: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    hist = get_user_history(user_id=user_id, conn=conn, limit=limit)
    res = []
    for h in hist:
        res.append({
            "entry_id": h["turn_id"],
            "timestamp": h["created_at"],
            "query_text": h["query_text"],
            "response_summary": h["response_summary"],
            "referenced_entities": h["last_discussed_wells"],
        })
    return res
