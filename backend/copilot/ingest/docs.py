import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.copilot.config import get_dataset_roots


def chunk_markdown_file(file_path: Path, base_rel: Path) -> List[Dict[str, Any]]:
    """Chunk a markdown manual or SOP into section-level indexed fragments."""
    text = file_path.read_text(encoding="utf-8")
    rel_path = str(file_path.relative_to(base_rel)).replace("\\", "/")

    # Extract Document ID and Title
    doc_id_match = re.search(r"Document ID:\s*([^\s·]+)", text, re.I)
    doc_code = doc_id_match.group(1).strip() if doc_id_match else file_path.stem.upper()

    title_match = re.search(r"^#\s+(.+)$", text, re.M)
    doc_title = title_match.group(1).strip() if title_match else file_path.stem

    # Split by ## or ### headers
    chunks: List[Dict[str, Any]] = []
    sections = re.split(r"(?m)^(?=#{2,3}\s+)", text)

    for idx, sec in enumerate(sections):
        sec_text = sec.strip()
        if not sec_text:
            continue
        m_head = re.match(r"^(#{2,3})\s+(.+)$", sec_text, re.M)
        if m_head:
            sec_title = m_head.group(2).strip()
            # Clean section anchor (e.g. "9.3 Production temperature rule" -> "9.3")
            num_match = re.match(r"^(\d+(?:\.\d+)?|[A-Z]+-\d+)", sec_title)
            sec_anchor = num_match.group(1) if num_match else f"sec-{idx}"
        else:
            sec_title = "Overview"
            sec_anchor = "overview"

        chunk_id = f"DOC:{doc_code}#{sec_anchor}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_code": doc_code,
            "title": doc_title,
            "section": sec_title,
            "content": sec_text,
            "source_file": rel_path,
        })

    return chunks


def extract_all_doc_chunks() -> List[Dict[str, Any]]:
    """Scan all SOPs and manuals across dataset roots and extract chunks."""
    all_chunks: List[Dict[str, Any]] = []
    roots = get_dataset_roots()
    seen_ids = set()

    for root in roots:
        fleet_dir = root / "fleet"
        if not fleet_dir.exists():
            continue
        for md_file in sorted(fleet_dir.rglob("*.md")):
            for c in chunk_markdown_file(md_file, root):
                if c["chunk_id"] not in seen_ids:
                    seen_ids.add(c["chunk_id"])
                    all_chunks.append(c)

    return all_chunks


def init_doc_fts(conn: sqlite3.Connection) -> None:
    """Initialize SQLite FTS5 table for doc chunks."""
    conn.execute("DROP TABLE IF EXISTS doc_chunks")
    conn.execute("DROP TABLE IF EXISTS doc_chunks_fts")
    
    conn.execute("""
        CREATE TABLE doc_chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_code TEXT,
            title TEXT,
            section TEXT,
            content TEXT,
            source_file TEXT
        )
    """)
    
    conn.execute("""
        CREATE VIRTUAL TABLE doc_chunks_fts USING fts5(
            chunk_id UNINDEXED,
            doc_code,
            title,
            section,
            content,
            content='doc_chunks',
            content_rowid='rowid'
        )
    """)


def index_doc_chunks(conn: sqlite3.Connection, chunks: List[Dict[str, Any]]) -> int:
    """Index chunks into doc_chunks and FTS5 table."""
    conn.executemany("""
        INSERT OR REPLACE INTO doc_chunks (chunk_id, doc_code, title, section, content, source_file)
        VALUES (:chunk_id, :doc_code, :title, :section, :content, :source_file)
    """, chunks)

    # Rebuild FTS index
    conn.execute("INSERT INTO doc_chunks_fts(doc_chunks_fts) VALUES('rebuild')")
    conn.commit()
    return len(chunks)


def search_docs(conn: sqlite3.Connection, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search documentation chunks using FTS5."""
    clean_q = re.sub(r"[^\w\s]", " ", query).strip()
    if not clean_q:
        return []
    terms = " OR ".join([f'"{t}"' for t in clean_q.split() if len(t) > 2])
    if not terms:
        terms = f'"{clean_q}"'

    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.chunk_id, c.doc_code, c.title, c.section, c.content, c.source_file, rank
        FROM doc_chunks_fts f
        JOIN doc_chunks c ON f.rowid = c.rowid
        WHERE doc_chunks_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (terms, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "chunk_id": row[0],
            "doc_code": row[1],
            "title": row[2],
            "section": row[3],
            "snippet": row[4][:300],
            "source_file": row[5],
        })
    return results
