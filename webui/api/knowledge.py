"""Iris 个人文档知识库 — SQLite FTS5 + hermes cjk_unicode61 中文分词。

上传文档 → 分块索引 → 对话中 agent 经 kb_search 工具自动检索。
零第三方依赖：标准库 sqlite3 + hermes_state_fts.load_fts5_cjk_extension。
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_KB_NAME = "knowledge.db"
_SUPPORTED_EXTS = {".txt", ".md", ".markdown", ".json", ".csv", ".log", ".yaml", ".yml"}
_MAX_CHUNK = 1000  # 每块最大字符数


def _home_dir() -> Path:
    env = os.environ.get("HERMES_HOME")
    return Path(env) if env else Path.home() / ".hermes"


def _db_path() -> Path:
    return _home_dir() / _KB_NAME


def _docs_dir() -> Path:
    d = _home_dir() / "knowledge"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(_db_path()), timeout=8)
    con.row_factory = sqlite3.Row
    try:
        from hermes_state_fts import load_fts5_cjk_extension
        load_fts5_cjk_extension(con)
    except Exception:  # noqa: BLE001
        pass
    return con


def _ensure_db(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS documents ("
        " doc_id TEXT PRIMARY KEY, title TEXT, filename TEXT, ext TEXT,"
        " size INTEGER, created REAL, chunk_count INTEGER)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS chunks ("
        " chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT,"
        " seq INTEGER, content TEXT)")
    # 优先 hermes 原生 cjk_unicode61（中文精确），.so 缺失时降级 SQLite 内置 trigram
    try:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(content, tokenize='cjk_unicode61')")
    except sqlite3.OperationalError:
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(content, tokenize='trigram')")
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id, seq)")
    con.commit()


def _split_chunks(text: str) -> list[str]:
    """按段落 + 长度上限分块（保留语义完整性）。"""
    text = re.sub(r"\r\n?", "\n", text or "")
    # 先按空行分段
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        # 超长段落内部再切
        while len(p) > _MAX_CHUNK:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(p[:_MAX_CHUNK])
            p = p[_MAX_CHUNK:]
        if len(buf) + len(p) + 1 <= _MAX_CHUNK:
            buf = (buf + "\n" + p).strip() if buf else p
        else:
            chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks


def upload_document(filename: str, data: bytes) -> dict:
    """保存文档并建立索引。filename 未提供时返回错误。"""
    if not filename:
        return {"ok": False, "error": "missing filename"}
    name = Path(filename).name
    ext = Path(name).suffix.lower()
    if ext not in _SUPPORTED_EXTS:
        return {
            "ok": False,
            "error": f"unsupported extension {ext}; supported: {', '.join(sorted(_SUPPORTED_EXTS))}",
        }
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"decode failed: {exc}"}
    doc_id = uuid.uuid4().hex[:12]
    # 保留原文件
    target = _docs_dir() / f"{doc_id}{ext}"
    try:
        target.write_bytes(data)
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    chunks = _split_chunks(text)
    title = name
    con = _connect()
    try:
        _ensure_db(con)
        con.execute(
            "INSERT INTO documents (doc_id, title, filename, ext, size, created, chunk_count)"
            " VALUES (?,?,?,?,?,?,?)",
            (doc_id, title, name, ext, len(data), time.time(), len(chunks)))
        for i, c in enumerate(chunks):
            cur = con.execute("INSERT INTO chunks (doc_id, seq, content) VALUES (?,?,?)",
                              (doc_id, i, c))
            con.execute("INSERT INTO chunk_fts (rowid, content) VALUES (?,?)",
                        (cur.lastrowid, c))
        con.commit()
    except Exception as exc:  # noqa: BLE001
        con.rollback()
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        return {"ok": False, "error": f"index failed: {exc}"}
    finally:
        con.close()
    return {"ok": True, "doc_id": doc_id, "title": title, "chunks": len(chunks)}


def list_documents() -> dict:
    try:
        con = _connect()
        _ensure_db(con)
        rows = con.execute(
            "SELECT doc_id, title, filename, size, created, chunk_count FROM documents"
            " ORDER BY created DESC").fetchall()
        con.close()
        return {
            "ok": True,
            "documents": [
                {
                    "doc_id": r["doc_id"], "title": r["title"], "filename": r["filename"],
                    "size": r["size"], "created": r["created"], "chunks": r["chunk_count"],
                }
                for r in rows
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": True, "documents": [], "error": str(exc)}


def delete_document(doc_id: str) -> dict:
    try:
        con = _connect()
        _ensure_db(con)
        row = con.execute("SELECT filename FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        con.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
        con.execute("DELETE FROM chunk_fts WHERE rowid IN (SELECT chunk_id FROM chunks WHERE doc_id=?)",
                    (doc_id,))
        con.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))
        con.commit()
        con.close()
        if row:
            ( _docs_dir() / f"{doc_id}{Path(row['filename']).suffix}" ).unlink(missing_ok=True)
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def search(query: str, top_k: int = 4) -> dict:
    q = (query or "").strip()
    if not q:
        return {"ok": True, "results": []}
    top_k = max(1, min(int(top_k or 4), 10))
    try:
        con = _connect()
        _ensure_db(con)
        safe = " ".join(w for w in q.replace('"', " ").split() if w) or q
        try:
            # trigram/cjk 对短语用 MATCH；短查询或特殊字符降级 LIKE
            if len(safe) >= 3:
                rows = con.execute(
                    "SELECT d.title AS doc, c.content, bm25(chunk_fts) AS rank "
                    "FROM chunk_fts JOIN chunks c ON c.chunk_id = chunk_fts.rowid "
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
                "SELECT d.title AS doc, c.content, 0.0 AS rank "
                "FROM chunks c JOIN documents d ON d.doc_id = c.doc_id "
                "WHERE c.content LIKE ? LIMIT ?",
                (like, top_k)).fetchall()
        con.close()
        return {
            "ok": True,
            "results": [
                {"doc": r["doc"], "content": (r["content"] or "")[:800], "rank": round(float(r["rank"]), 3)}
                for r in rows
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": True, "results": [], "error": str(exc)}
