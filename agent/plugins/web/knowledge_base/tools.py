"""kb_search 工具 — 检索 Iris 个人知识库（SQLite FTS5 + cjk_unicode61）。"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_NAME = "knowledge.db"


def _db_path() -> Path:
    home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(home) / _DB_NAME


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(_db_path()), timeout=8)
    con.row_factory = sqlite3.Row
    try:
        from hermes_state_fts import load_fts5_cjk_extension
        load_fts5_cjk_extension(con)
    except Exception:  # noqa: BLE001
        pass
    try:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(content, tokenize='cjk_unicode61')")
    except sqlite3.OperationalError:
        try:
            con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(content, tokenize='trigram')")
        except sqlite3.OperationalError:
            pass
    return con


def _search(query: str, top_k: int = 4) -> dict:
    q = (query or "").strip()
    if not q:
        return {"results": [], "error": "empty query"}
    top_k = max(1, min(int(top_k or 4), 10))
    try:
        con = _connect()
        # FTS5 MATCH：>=3 字符用 phrase（trigram/cjk），短词或特殊字符降级 LIKE
        safe = " ".join(w for w in q.replace('"', " ").split() if w) or q
        try:
            if len(safe) >= 3:
                rows = con.execute(
                    "SELECT d.title AS doc, c.chunk_id, c.content, bm25(chunk_fts) AS rank "
                    "FROM chunk_fts "
                    "JOIN chunks c ON c.chunk_id = chunk_fts.rowid "
                    "JOIN documents d ON d.doc_id = c.doc_id "
                    "WHERE chunk_fts MATCH ? ORDER BY rank LIMIT ?",
                    ('"'+safe.replace('"', '""')+'"', top_k)).fetchall()
            else:
                rows = []
        except sqlite3.OperationalError:
            rows = []
        if not rows:
            like = "%" + safe + "%"
            rows = con.execute(
                "SELECT d.title AS doc, c.chunk_id, c.content, 0.0 AS rank "
                "FROM chunks c JOIN documents d ON d.doc_id = c.doc_id "
                "WHERE c.content LIKE ? LIMIT ?",
                (like, top_k)).fetchall()
        con.close()
        results = [
            {"doc": r["doc"], "content": (r["content"] or "")[:800], "rank": round(float(r["rank"]), 3)}
            for r in rows
        ]
        return {"results": results}
    except Exception as exc:  # noqa: BLE001
        logger.warning("kb_search failed: %s", exc)
        return {"results": [], "error": str(exc)}


def register_tools(ctx) -> None:
    ctx.register_tool(
        name="kb_search",
        toolset="knowledge_base",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "要在个人知识库中检索的关键词或问题"},
                "top_k": {"type": "integer", "description": "返回的匹配片段数量，默认 4"},
            },
            "required": ["query"],
        },
        handler=lambda args: _search(args.get("query", ""), args.get("top_k", 4)),
        description=(
            "Search the user's personal knowledge base (documents they uploaded) "
            "and return matching excerpts with document titles. Use when the user "
            "asks about content in their uploaded documents or personal notes."
        ),
        emoji="📚",
    )
