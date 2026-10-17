import sqlite3
from typing import Any, Dict, List, Optional
from backend.copilot.db import get_connection
from backend.copilot.ingest.docs import search_docs
from backend.copilot.tools.render import render_evidence


def tool_search_documentation(
    query: str,
    limit: int = 5,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Search SOPs and operating manuals using SQLite FTS5.
    
    Returns structured chunks with section citations and visual evidence block.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        chunks = search_docs(conn, query, limit=limit)
        evidence_ids = [c["chunk_id"] for c in chunks]

        evidence_items = [
            {
                "id": c["chunk_id"],
                "title": f"{c['doc_code']} — {c['section']}",
                "snippet": c.get("snippet", ""),
                "source": c.get("source_file", ""),
            }
            for c in chunks
        ]

        visual = render_evidence(
            title=f"Documentation Results for '{query}'",
            evidence_items=evidence_items,
            evidence_ids=evidence_ids,
        )

        return {
            "query": query,
            "results_count": len(chunks),
            "chunks": chunks,
            "evidence_ids": evidence_ids,
            "visual": visual,
        }
    finally:
        if close_conn:
            conn.close()
