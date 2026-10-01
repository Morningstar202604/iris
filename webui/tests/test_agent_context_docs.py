from pathlib import Path


def test_root_does_not_shadow_agents_md_with_iris_context_file():
    repo_root = Path(__file__).resolve().parents[1]

    for name in ("IRIS.md", ".iris.md"):
        assert not (repo_root / name).exists(), (
            f"{name} at the repository root is auto-loaded by Iris Agent as "
            "project context before AGENTS.md; long human-facing Iris overview "
            "docs belong under docs/."
        )


def test_why_iris_doc_remains_linked_from_readme():
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert (repo_root / "docs" / "why-iris.md").exists()
    assert "docs/why-iris.md" in readme
    assert "[IRIS.md](IRIS.md)" not in readme
