"""User-scoped Mem0 memory with a private SQLite search fallback.

SQLite remains the synchronous source of truth for recent turns and well IDs.
Mem0 augments it with long-term semantic retrieval when MEM0_API_KEY is set.
"""
from __future__ import annotations

import os
import re
import sqlite3
from typing import Any, Dict, Iterable, List, Optional


class Mem0Adapter:
    """Thin, failure-tolerant adapter around Mem0's hosted MemoryClient API."""

    def __init__(self, memory: Any = None, api_key: Optional[str] = None):
        raw_key = (api_key or os.getenv("MEM0_API_KEY") or "").strip()
        self.api_key = raw_key if raw_key and not raw_key.lower().startswith("your_") else None
        self.memory = memory
        self.last_error: Optional[str] = None
        if self.memory is None and self.api_key:
            try:
                from mem0 import MemoryClient

                self.memory = MemoryClient(api_key=self.api_key)
            except Exception as exc:  # Optional dependency or unavailable configuration.
                self.last_error = type(exc).__name__

    @property
    def remote_enabled(self) -> bool:
        return self.memory is not None

    @property
    def engine_name(self) -> str:
        return "sqlite+mem0" if self.remote_enabled else "sqlite"

    @staticmethod
    def _require_user_id(user_id: str) -> str:
        scoped_user_id = str(user_id or "").strip()
        if not scoped_user_id:
            raise ValueError("user_id is required for private memory operations")
        return scoped_user_id

    @staticmethod
    def _as_results(response: Any) -> List[Dict[str, Any]]:
        if isinstance(response, dict):
            rows = response.get("results", response.get("memories", []))
        elif isinstance(response, list):
            rows = response
        else:
            rows = getattr(response, "results", [])
        if isinstance(rows, dict):
            rows = [rows]
        normalized: List[Dict[str, Any]] = []
        for row in rows or []:
            if isinstance(row, dict):
                normalized.append(dict(row))
            elif hasattr(row, "__dict__"):
                normalized.append(vars(row))
        return normalized

    def add(self, messages: Any, user_id: str) -> Dict[str, Any]:
        """Send conversational messages to Mem0 with mandatory user scoping.

        Local-only mode is intentionally a no-op here because the caller records
        every turn synchronously in SQLite before invoking this adapter.
        """
        scoped_user_id = self._require_user_id(user_id)
        if self.memory is None:
            return {"stored": False, "engine": "sqlite", "fallback": True}
        try:
            result = self.memory.add(messages, user_id=scoped_user_id)
            return {"stored": True, "engine": "mem0", "result": result}
        except Exception as exc:
            self.last_error = type(exc).__name__
            return {"stored": False, "engine": "sqlite", "fallback": True}

    def _search_sqlite(
        self,
        query: str,
        user_id: str,
        conn: Optional[sqlite3.Connection],
        limit: int,
    ) -> List[Dict[str, Any]]:
        close_conn = False
        if conn is None:
            try:
                from backend.copilot.db import get_connection

                conn = get_connection()
                close_conn = True
            except Exception:
                return []
        try:
            tokens = list(dict.fromkeys(re.findall(r"[A-Za-z0-9_-]+", query.lower())))
            if not tokens:
                return []
            clauses = []
            params: List[Any] = [user_id]
            for token in tokens[:12]:
                clauses.append(
                    "(lower(query_text) LIKE ? OR lower(COALESCE(response_summary, '')) LIKE ? "
                    "OR lower(COALESCE(last_discussed_wells_json, '')) LIKE ?)"
                )
                escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                pattern = f"%{escaped}%"
                params.extend([pattern, pattern, pattern])
            sql = """
                SELECT query_text, response_summary, last_discussed_wells_json, created_at
                FROM user_messages
                WHERE user_id = ? AND (""" + " OR ".join(clauses) + ") ORDER BY created_at DESC LIMIT ?"
            params.append(max(1, min(int(limit), 20)))
            rows = conn.execute(sql, params).fetchall()
            output = []
            for row in rows:
                query_text = row["query_text"]
                summary = row["response_summary"] or ""
                wells = row["last_discussed_wells_json"] or "[]"
                memory_text = "; ".join(part for part in (query_text, summary, wells) if part)
                output.append({
                    "memory": memory_text,
                    "user_id": user_id,
                    "created_at": row["created_at"],
                    "source": "sqlite",
                })
            return output
        except (sqlite3.Error, KeyError, TypeError):
            # A fresh or partial database can lack memory tables; SQLite remains usable.
            return []
        finally:
            if close_conn and conn is not None:
                conn.close()

    def search(
        self,
        query: str,
        user_id: str,
        conn: Optional[sqlite3.Connection] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Fuse user-scoped Mem0 semantic matches with SQLite turn recall."""
        scoped_user_id = self._require_user_id(user_id)
        results: List[Dict[str, Any]] = []
        if self.memory is not None and query.strip():
            try:
                response = self.memory.search(query, user_id=scoped_user_id)
                for item in self._as_results(response):
                    result_user_id = item.get("user_id")
                    # Defend against mixed-tenant responses even if the provider misbehaves.
                    if result_user_id is not None and str(result_user_id) != scoped_user_id:
                        continue
                    memory_text = item.get("memory") or item.get("text") or item.get("content")
                    if memory_text:
                        results.append({**item, "memory": str(memory_text), "user_id": scoped_user_id, "source": "mem0"})
            except Exception as exc:
                self.last_error = type(exc).__name__

        results.extend(self._search_sqlite(query, scoped_user_id, conn, limit))
        unique: List[Dict[str, Any]] = []
        seen = set()
        for item in results:
            normalized = str(item.get("memory", "")).strip()
            key = normalized.casefold()
            if normalized and key not in seen:
                unique.append(item)
                seen.add(key)
            if len(unique) >= max(1, min(int(limit), 20)):
                break
        return unique
