import sqlite3
from typing import Any, Dict, List, Optional
from backend.copilot.db import get_connection
from backend.copilot.domain.hybrid_search import run_hybrid_search
from backend.copilot.tools.render import render_evidence


def tool_search_documentation(
    query: str,
    limit: int = 5,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Search SOPs, operating manuals, maintenance reports, and notes using Hybrid RRF.
    
    Combines SQLite FTS5 BM25 keyword matching with in-memory TF-IDF Cosine similarity.
    Returns structured results with exact citations and generative UI evidence block.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        search_res = run_hybrid_search(query, limit=limit, conn=conn)
        results = search_res["results"]
        evidence_ids = search_res["evidence_ids"]

        chunks = [
            {
                "chunk_id": r["citation_id"],
                "doc_code": r["title"].split("—")[0].strip() if "—" in r["title"] else r["title"],
                "title": r["title"],
                "section": r["title"],
                "snippet": r["snippet"],
                "source_file": r["source_file"],
                "score": r["score"],
            }
            for r in results
        ]

        evidence_items = [
            {
                "id": r["citation_id"],
                "title": r["title"],
                "snippet": r["snippet"],
                "source": f"{r['source_file']} (RRF Score: {r['score']})",
            }
            for r in results
        ]

        visual = render_evidence(
            title=f"Hybrid Search Results for '{query}'",
            evidence_items=evidence_items,
            evidence_ids=evidence_ids,
        )

        return {
            "query": query,
            "results_count": len(results),
            "chunks": chunks,
            "results": results,
            "evidence_ids": evidence_ids,
            "visual": visual,
        }
    finally:
        if close_conn:
            conn.close()
