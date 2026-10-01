"""Knowledge store contract (ledger R1-R4).

The knowledge store is written by the WebUI and read by the agent's
`kb_search` tool, so its home must come from the same profile resolver the
rest of the server uses, failures must be reported as failures, and a
malformed `top_k` must not escape the handler.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def knowledge_home(tmp_path, monkeypatch):
    """Put the store in a temp home for both the old env read and the resolver."""
    home = tmp_path / "kb-home"
    home.mkdir()
    monkeypatch.setenv("IRIS_HOME", str(home))

    import api.profiles as profiles

    monkeypatch.setattr(profiles, "get_active_iris_home", lambda: home)

    from api import knowledge

    return knowledge, home


def test_home_dir_follows_profile_resolver(tmp_path, monkeypatch):
    base = tmp_path / ".iris"
    (base / "profiles" / "p2").mkdir(parents=True)
    monkeypatch.setenv("IRIS_BASE_HOME", str(base))
    monkeypatch.delenv("IRIS_HOME", raising=False)

    import api.profiles as profiles

    monkeypatch.setattr(profiles, "_DEFAULT_IRIS_HOME", base)
    try:
        profiles.set_request_profile("p2")
        from api import knowledge

        expected = profiles.get_iris_home_for_profile("p2")
        assert expected != Path.home() / ".iris", (
            "premise: resolver must differ from the fallback"
        )
        assert knowledge._home_dir() == expected
    finally:
        profiles.clear_request_profile()


def test_home_dir_uses_resolver_even_when_env_is_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("IRIS_HOME", raising=False)

    import api.profiles as profiles

    resolved = tmp_path / "resolved-home"
    monkeypatch.setattr(profiles, "get_active_iris_home", lambda: resolved)

    from api import knowledge

    assert knowledge._home_dir() == resolved


def test_delete_document_removes_fts_rows(knowledge_home):
    knowledge, home = knowledge_home
    knowledge._connect  # module attribute sanity
    uploaded = knowledge.upload_document(
        "notes.txt", b"alpha beta gamma\n\ndelta epsilon"
    )
    assert uploaded["ok"] is True
    doc_id = uploaded["doc_id"]

    con = knowledge._connect()
    before = con.execute("SELECT COUNT(*) FROM chunk_fts").fetchone()[0]
    con.close()
    assert before > 0

    assert knowledge.delete_document(doc_id)["ok"] is True

    con = knowledge._connect()
    remaining_chunks = con.execute(
        "SELECT COUNT(*) FROM chunks WHERE doc_id=?", (doc_id,)
    ).fetchone()[0]
    remaining_fts = con.execute("SELECT COUNT(*) FROM chunk_fts").fetchone()[0]
    con.close()
    assert remaining_chunks == 0
    assert remaining_fts == 0, "FTS rows must be removed together with their chunks"


def test_list_documents_reports_failure_as_failure(monkeypatch):
    from api import knowledge

    def boom():
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(knowledge, "_connect", boom)
    result = knowledge.list_documents()

    assert result["ok"] is False
    assert result.get("error")


def test_search_reports_failure_as_failure(monkeypatch):
    from api import knowledge

    def boom():
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(knowledge, "_connect", boom)
    result = knowledge.search("anything", 4)

    assert result["ok"] is False
    assert result.get("error")


def test_search_non_numeric_top_k_does_not_escape(knowledge_home):
    knowledge, _ = knowledge_home

    result = knowledge.search("anything", "abc")

    assert isinstance(result, dict)
    assert "results" in result


def test_upload_search_delete_roundtrip(knowledge_home):
    knowledge, _ = knowledge_home

    uploaded = knowledge.upload_document(
        "readme.md", b"# Iris\n\npersonal notes about iris"
    )
    assert uploaded["ok"] is True
    doc_id = uploaded["doc_id"]

    found = knowledge.search("iris", 4)
    assert found["ok"] is True
    assert found["results"], "indexed content must be searchable"

    listing = knowledge.list_documents()
    assert listing["ok"] is True
    assert any(d["doc_id"] == doc_id for d in listing["documents"])

    assert knowledge.delete_document(doc_id)["ok"] is True
    assert knowledge.list_documents()["documents"] == []
