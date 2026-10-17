import math
import re
import sqlite3
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from backend.copilot.db import get_connection


class HybridRRFSearchEngine:
    """
    Hybrid Search combining SQLite FTS5 BM25 Keyword Search with
    In-Memory Subword/Word N-Gram TF-IDF Cosine Similarity, merged via
    Reciprocal Rank Fusion (RRF):

        RRF_Score(d) = 1 / (60 + rank_FTS5(d)) + 1 / (60 + rank_Cosine(d))
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self.conn = conn or get_connection()
        self._corpus: List[Dict[str, Any]] = []
        self._doc_vectors: List[Counter] = []
        self._doc_norms: List[float] = []
        self._idf: Dict[str, float] = {}
        self._is_indexed = False
        self._build_in_memory_index()

    def _tokenize(self, text: str) -> List[str]:
        """Extract lowercased word tokens plus character 3-grams for typo & morphological tolerance."""
        if not text:
            return []
        low = text.lower()
        words = re.findall(r"\b[a-z0-9_-]{2,}\b", low)
        # Subword 3-grams
        ngrams = [low[i:i + 3] for i in range(len(low) - 2) if " " not in low[i:i + 3] and "\n" not in low[i:i + 3]]
        return words + ngrams[:100]

    def _build_in_memory_index(self) -> None:
        """Load documents across SOPs, manuals, maintenance records, and context notes."""
        if self._is_indexed:
            return

        cursor = self.conn.cursor()

        # 1. Documentation chunks (SOPs, manuals)
        try:
            cursor.execute("SELECT chunk_id, doc_code, title, section, content, source_file FROM doc_chunks")
            for r in cursor.fetchall():
                self._corpus.append({
                    "id": r["chunk_id"],
                    "source_type": "doc",
                    "title": f"{r['doc_code']} — {r['section']}",
                    "content": r["content"],
                    "source_file": r["source_file"],
                    "citation_id": r["chunk_id"],
                })
        except Exception:
            pass

        # 2. Maintenance records
        try:
            cursor.execute("""
                SELECT maintenance_id, asset_id, equipment_kind, issue, action_taken, maintenance_type
                FROM maintenance
            """)
            for r in cursor.fetchall():
                text = f"Maintenance on {r['asset_id']} ({r['equipment_kind']}): {r['issue']} | Action: {r['action_taken']} ({r['maintenance_type']})"
                self._corpus.append({
                    "id": r["maintenance_id"],
                    "source_type": "maintenance",
                    "title": f"{r['maintenance_id']} — {r['asset_id']} {r['equipment_kind']}",
                    "content": text,
                    "source_file": "maintenance.csv",
                    "citation_id": r["maintenance_id"],
                })
        except Exception:
            pass

        # 3. Context notes
        try:
            cursor.execute("SELECT note_id, asset_id, author_user_id, note_type, text FROM context_notes")
            for r in cursor.fetchall():
                text = f"Operator Note {r['note_id']} for {r['asset_id']} by {r['author_user_id']}: {r['text']}"
                self._corpus.append({
                    "id": r["note_id"],
                    "source_type": "context_note",
                    "title": f"{r['note_id']} — {r['asset_id']}",
                    "content": text,
                    "source_file": "context_notes.json",
                    "citation_id": r["note_id"],
                })
        except Exception:
            pass

        # Compute TF-IDF
        num_docs = len(self._corpus)
        if num_docs == 0:
            return

        doc_freqs: Counter = Counter()
        for doc in self._corpus:
            tokens = self._tokenize(f"{doc['title']} {doc['content']}")
            tf = Counter(tokens)
            self._doc_vectors.append(tf)
            for t in set(tokens):
                doc_freqs[t] += 1

        for term, df in doc_freqs.items():
            self._idf[term] = math.log((num_docs + 1) / (df + 1)) + 1.0

        # Precompute L2 norms for cosine similarity
        for tf in self._doc_vectors:
            norm_sq = sum((count * self._idf.get(term, 1.0)) ** 2 for term, count in tf.items())
            self._doc_norms.append(math.sqrt(norm_sq) if norm_sq > 0 else 1.0)

        self._is_indexed = True

    def search_fts5(self, query: str, limit: int = 50) -> List[Tuple[str, int, float]]:
        """Run SQLite FTS5 query on doc_chunks returning list of (doc_id, rank_index, raw_score)."""
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        if not clean_q:
            return []

        terms = " OR ".join([f'"{t}"' for t in clean_q.split() if len(t) > 2])
        if not terms:
            terms = f'"{clean_q}"'

        cursor = self.conn.cursor()
        results = []
        try:
            cursor.execute("""
                SELECT c.chunk_id, rank
                FROM doc_chunks_fts f
                JOIN doc_chunks c ON f.rowid = c.rowid
                WHERE doc_chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (terms, limit))
            for rank_idx, row in enumerate(cursor.fetchall(), start=1):
                results.append((row[0], rank_idx, float(row[1])))
        except Exception:
            pass

        return results

    def search_cosine(self, query: str, limit: int = 50) -> List[Tuple[str, int, float]]:
        """Run subword/word TF-IDF Cosine similarity over in-memory corpus."""
        tokens = self._tokenize(query)
        if not tokens:
            return []

        q_tf = Counter(tokens)
        q_norm_sq = sum((count * self._idf.get(term, 1.0)) ** 2 for term, count in q_tf.items())
        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0

        scores: List[Tuple[int, float]] = []
        for idx, (doc_tf, doc_norm) in enumerate(zip(self._doc_vectors, self._doc_norms)):
            dot_product = 0.0
            for term, q_cnt in q_tf.items():
                if term in doc_tf:
                    w = self._idf.get(term, 1.0)
                    dot_product += (q_cnt * w) * (doc_tf[term] * w)

            if dot_product > 0.0:
                sim = dot_product / (q_norm * doc_norm)
                scores.append((idx, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:limit]

        results = []
        for rank_idx, (doc_idx, sim) in enumerate(top, start=1):
            results.append((self._corpus[doc_idx]["id"], rank_idx, sim))

        return results

    def hybrid_search(
        self,
        query: str,
        limit: int = 5,
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Search using Reciprocal Rank Fusion (RRF).
        Returns top `limit` items with combined RRF score and verified citations.
        """
        fts_ranks = {doc_id: rank for doc_id, rank, _ in self.search_fts5(query, limit=limit * 5)}
        cosine_ranks = {doc_id: rank for doc_id, rank, _ in self.search_cosine(query, limit=limit * 5)}

        all_doc_ids = set(fts_ranks.keys()).union(cosine_ranks.keys())
        if not all_doc_ids:
            return []

        rrf_scores: List[Tuple[str, float, int, int]] = []
        PENALTY_RANK = 1000

        for doc_id in all_doc_ids:
            r_fts = fts_ranks.get(doc_id, PENALTY_RANK)
            r_cos = cosine_ranks.get(doc_id, PENALTY_RANK)
            rrf = (1.0 / (k + r_fts)) + (1.0 / (k + r_cos))
            rrf_scores.append((doc_id, rrf, r_fts, r_cos))

        rrf_scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = rrf_scores[:limit]

        # Lookup details from corpus
        corpus_map = {d["id"]: d for d in self._corpus}
        results = []

        for doc_id, score, r_fts, r_cos in top_candidates:
            doc = corpus_map.get(doc_id)
            if not doc:
                continue

            results.append({
                "id": doc["id"],
                "citation_id": doc["citation_id"],
                "source_type": doc["source_type"],
                "title": doc["title"],
                "snippet": doc["content"][:350],
                "score": round(score, 5),
                "fts5_rank": r_fts if r_fts != PENALTY_RANK else None,
                "cosine_rank": r_cos if r_cos != PENALTY_RANK else None,
                "source_file": doc["source_file"],
                "evidence_ids": [doc["citation_id"]],
            })

        return results


def run_hybrid_search(
    query: str,
    limit: int = 5,
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Execute hybrid RRF search across documentation, maintenance, and context notes."""
    engine = HybridRRFSearchEngine(conn=conn)
    results = engine.hybrid_search(query, limit=limit)
    evidence_ids = sorted(list(set([r["citation_id"] for r in results])))

    evidence_items = [
        {
            "id": r["citation_id"],
            "title": r["title"],
            "snippet": r["snippet"],
            "source": f"{r['source_file']} (RRF Score: {r['score']})",
        }
        for r in results
    ]

    from backend.copilot.tools.render import render_evidence
    visual = render_evidence(
        title=f"Hybrid Semantic & Keyword Search: '{query}'",
        evidence_items=evidence_items,
        evidence_ids=evidence_ids,
    )

    return {
        "query": query,
        "results_count": len(results),
        "results": results,
        "evidence_ids": evidence_ids,
        "visual": visual,
    }
