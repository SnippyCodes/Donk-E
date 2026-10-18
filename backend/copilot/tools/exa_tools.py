"""Tool wrappers for external Exa semantic research."""
from typing import Any, Dict, Optional

from src.domain.exa_search import search_external_oilfield_knowledge


def tool_search_external_oilfield_knowledge(
    query: str = "",
    limit: int = 5,
    conn: Optional[Any] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Search external oilfield sources; local manuals remain in search_documentation."""
    response = search_external_oilfield_knowledge(query, limit=limit)
    results = response.get("results", [])
    evidence_ids = [row["citation_id"] for row in results if row.get("citation_id")]
    evidence_items = [
        {
            "id": row["citation_id"],
            "title": row["title"],
            "snippet": row.get("text", ""),
            "source": row["url"],
            "url": row["url"],
        }
        for row in results
    ]
    return {
        **response,
        "search_engine": "exa" if response.get("status") == "ok" else "offline",
        "results_count": len(results),
        "evidence_ids": evidence_ids,
        "visual": {
            "block_type": "evidence",
            "title": f"Exa External Search: {query}",
            "evidence_items": evidence_items,
            "evidence_ids": evidence_ids,
        } if results else None,
    }
