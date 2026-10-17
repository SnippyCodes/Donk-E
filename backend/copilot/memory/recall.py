"""
recall.py — Per-user private recall for conversation memory.

Each user has a private conversation log. Recall queries enforce
WHERE user_id = ? so one user cannot access another's history.
"""
import datetime
import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from backend.copilot.db import get_connection


def save_interaction(
    conn: sqlite3.Connection,
    user_id: str,
    query_text: str,
    response_summary: str,
    referenced_entities: Optional[List[str]] = None,
) -> str:
    """
    Record a user's query and the referenced entities for future recall.

    Args:
        conn: Active SQLite connection
        user_id: The user whose private memory this is
        query_text: What the user asked
        response_summary: Brief summary of the response
        referenced_entities: List of entity IDs mentioned (well IDs, area IDs, etc.)

    Returns:
        The entry_id of the saved interaction.
    """
    entry_id = f"RECALL-{uuid.uuid4().hex[:12]}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    entities_json = json.dumps(referenced_entities or [])

    with conn:
        conn.execute("""
            INSERT INTO user_recall (entry_id, user_id, timestamp, query_text, response_summary, referenced_entities_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entry_id, user_id, timestamp, query_text, response_summary, entities_json))

    return entry_id


def recall_entities(
    conn: sqlite3.Connection,
    user_id: str,
    lookback_days: int = 7,
    entity_type: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve entities from a user's private recall memory.
    STRICTLY enforces user_id filtering — one user cannot see another's history.

    Args:
        conn: Active SQLite connection
        user_id: The user whose recall to search (code-enforced, never from LLM)
        lookback_days: How far back to look
        entity_type: Optional filter like "WELL" to only return well IDs
        limit: Max entries to return

    Returns:
        List of past interactions with their referenced entities.
    """
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)).isoformat().replace("+00:00", "Z")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT entry_id, timestamp, query_text, response_summary, referenced_entities_json
        FROM user_recall
        WHERE user_id = ?
          AND timestamp >= ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, cutoff, limit))

    results = []
    for row in cursor.fetchall():
        entities = json.loads(row["referenced_entities_json"] or "[]")

        # Optional filter by entity type prefix
        if entity_type:
            entities = [e for e in entities if e.startswith(entity_type)]

        if entities or not entity_type:
            results.append({
                "entry_id": row["entry_id"],
                "timestamp": row["timestamp"],
                "query_text": row["query_text"],
                "response_summary": row["response_summary"],
                "referenced_entities": entities,
            })

    return results


def recall_wells(
    conn: sqlite3.Connection,
    user_id: str,
    lookback_days: int = 7,
) -> List[str]:
    """
    Shorthand: return unique well IDs from a user's recent conversations.
    Enforces private recall via WHERE user_id = ?.
    """
    entries = recall_entities(conn, user_id, lookback_days, entity_type="WELL")
    wells = []
    seen = set()
    for entry in entries:
        for e in entry["referenced_entities"]:
            if e not in seen:
                wells.append(e)
                seen.add(e)
    return wells


def has_conversation_history(
    conn: sqlite3.Connection,
    user_id: str,
    lookback_days: int = 7,
) -> bool:
    """Check if a user has any past conversation entries."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)).isoformat().replace("+00:00", "Z")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM user_recall
        WHERE user_id = ? AND timestamp >= ?
    """, (user_id, cutoff))
    return cursor.fetchone()[0] > 0
