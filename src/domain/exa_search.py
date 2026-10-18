"""Optional semantic web search for external oilfield/regulatory context.

Local SQLite FTS5/Hybrid RRF remains the primary search for fleet manuals and
maintenance reports. Exa is only used for explicitly external questions.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

try:  # Optional integration; offline installs do not need exa-py.
    from exa_py import Exa
except ImportError:  # pragma: no cover - exercised in environments without exa-py
    Exa = None  # type: ignore[assignment,misc]


def is_external_oilfield_query(query: str) -> bool:
    """Return true only for explicit external regulatory/industry research asks."""
    text = (query or "").lower()
    explicit_external = any(term in text for term in (
        "epa", "osha", "api rp 11l", "api recommended practice 11l",
        "industry benchmark", "industry benchmarks", "external regulation",
        "external regulatory", "regulatory context", "outside our sop",
        "outside local sop", "industry standard", "industry standards",
    ))
    spill_rules = any(term in text for term in (
        "spill regulation", "spill regulations", "spill rule", "spill rules",
        "spill reporting requirement", "spill reporting requirements",
    ))
    return explicit_external or spill_rules


def _field(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _offline(query: str) -> Dict[str, Any]:
    return {
        "status": "offline",
        "query": query,
        "results": [],
        "message": "External search is unavailable; no external sources were cited. Local documentation search remains available.",
    }


def search_external_oilfield_knowledge(
    query: str,
    limit: int = 5,
    *,
    client: Any = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Search Exa's neural index and return validated, citable external results.

    Missing credentials, optional dependency, or network errors return an empty
    offline result rather than raising or fabricating evidence.
    """
    clean_query = str(query or "").strip()
    if not clean_query:
        return {"status": "offline", "query": "", "results": [], "message": "A non-empty search query is required."}
    result_limit = max(1, min(int(limit), 10))
    raw_key = (api_key or os.getenv("EXA_API_KEY") or "").strip()
    key = raw_key if raw_key and not raw_key.lower().startswith("your_") else None
    if client is None:
        if not key or Exa is None:
            return _offline(clean_query)
        try:
            client = Exa(api_key=key)
        except Exception:
            return _offline(clean_query)

    try:
        response = client.search_and_contents(
            clean_query,
            type="neural",
            num_results=result_limit,
            text={"max_characters": 1200},
        )
    except Exception:
        # Older SDK versions expose search() with nested contents options.
        try:
            response = client.search(
                clean_query,
                type="neural",
                num_results=result_limit,
                contents={"text": {"max_characters": 1200}},
            )
        except Exception:
            return _offline(clean_query)

    rows = _field(response, "results", []) or []
    normalized: List[Dict[str, str]] = []
    seen_urls = set()
    for row in rows:
        title = re.sub(r"[\[\]|\r\n]+", " ", str(_field(row, "title", "External source"))).strip()
        url = str(_field(row, "url", "")).strip()
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or url in seen_urls:
            continue
        seen_urls.add(url)
        text = str(_field(row, "text", "") or _field(row, "summary", "")).strip()
        citation_id = f"EXA:{title}|{url}"
        normalized.append({
            "title": title or "External source",
            "url": url,
            "text": text[:1600],
            "citation_id": citation_id,
            "citation": f"[{citation_id}]",
        })
        if len(normalized) >= result_limit:
            break

    return {
        "status": "ok" if normalized else "no_results",
        "query": clean_query,
        "results": normalized,
        "message": "" if normalized else "Exa returned no usable external sources.",
    }
