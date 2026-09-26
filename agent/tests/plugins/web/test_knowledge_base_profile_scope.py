"""Knowledge-base plugin path and input contract.

Locks R1 (profile-aware home resolution) and R4 (`top_k` clamped inside the
handler) from the construction ledger.
"""

from __future__ import annotations

import sqlite3

from hermes_constants import (
    get_hermes_home,
    reset_hermes_home_override,
    set_hermes_home_override,
)

from plugins.web.knowledge_base import tools


def test_db_path_follows_context_local_override(tmp_path, monkeypatch):
    env_home = tmp_path / "profile-a"
    override_home = tmp_path / "profile-b"
    env_home.mkdir()
    override_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(env_home))

    token = set_hermes_home_override(override_home)
    try:
        assert tools._db_path() == override_home / "knowledge.db"
    finally:
        reset_hermes_home_override(token)


def test_db_path_uses_env_home_when_no_override(tmp_path, monkeypatch):
    home = tmp_path / "elsewhere"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    assert tools._db_path() == home / "knowledge.db"


def test_db_path_matches_canonical_home_when_env_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("HERMES_HOME", raising=False)
    assert tools._db_path() == get_hermes_home() / "knowledge.db"


def test_non_numeric_top_k_does_not_escape_handler(tmp_path, monkeypatch):
    home = tmp_path / "empty-home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))

    result = tools._search("anything", top_k="abc")

    assert isinstance(result, dict)
    assert "results" in result


def _seed(tmp_path, monkeypatch, chunk_count: int) -> None:
    home = tmp_path / "seeded-home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    con = sqlite3.connect(str(tools._db_path()))
    con.execute(
        "CREATE TABLE documents (doc_id TEXT PRIMARY KEY, title TEXT,"
        " filename TEXT, ext TEXT, size INTEGER, created REAL, chunk_count INTEGER)"
    )
    con.execute(
        "CREATE TABLE chunks (chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " doc_id TEXT, seq INTEGER, content TEXT)"
    )
    con.execute("CREATE VIRTUAL TABLE chunk_fts USING fts5(content)")
    con.execute(
        "INSERT INTO documents VALUES (?,?,?,?,?,?,?)",
        ("d1", "Doc One", "one.txt", ".txt", 10, 0.0, chunk_count),
    )
    for i in range(chunk_count):
        cur = con.execute(
            "INSERT INTO chunks (doc_id, seq, content) VALUES (?,?,?)",
            ("d1", i, f"needle chunk {i}"),
        )
        con.execute(
            "INSERT INTO chunk_fts (rowid, content) VALUES (?,?)",
            (cur.lastrowid, f"needle chunk {i}"),
        )
    con.commit()
    con.close()


def test_top_k_above_maximum_returns_at_most_ten(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, chunk_count=15)

    result = tools._search("needle", top_k=100)

    assert "error" not in result
    assert len(result["results"]) <= 10


def test_top_k_below_minimum_returns_at_least_one(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, chunk_count=5)

    result = tools._search("needle", top_k=0)

    assert "error" not in result
    assert len(result["results"]) >= 1
