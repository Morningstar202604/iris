"""pgvector Docker bootstrap must not expose a weakly-passworded database.

The setup wizard creates a local PostgreSQL container for mem0. The published
port must be loopback-only and the password must be generated per install —
a hardcoded password on a 0.0.0.0-published port is LAN-reachable.
"""

from __future__ import annotations

import subprocess

from plugins.memory.mem0 import _setup


def _run_ensure_pgvector(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_docker(*args, timeout, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(
        _setup, "_check_pgvector", lambda host, port: (False, "unreachable")
    )
    monkeypatch.setattr(_setup.shutil, "which", lambda name: "/usr/bin/docker")
    monkeypatch.setattr(_setup, "_docker", fake_docker)
    monkeypatch.setattr(_setup, "_pg_ready", lambda host, port, wait: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    config = _setup._ensure_pgvector()
    return calls, config


def _docker_run_args(calls: list[tuple[str, ...]]) -> list[str]:
    run_call = next(c for c in calls if c[0] == "run")
    return list(run_call)


def test_pgvector_container_publishes_on_loopback_only(monkeypatch):
    calls, _config = _run_ensure_pgvector(monkeypatch)
    run_args = _docker_run_args(calls)

    publish = run_args[run_args.index("-p") + 1]
    assert publish.startswith("127.0.0.1:"), f"port must bind loopback, got {publish!r}"


def test_pgvector_password_is_generated_not_hardcoded(monkeypatch):
    calls, config = _run_ensure_pgvector(monkeypatch)
    run_args = _docker_run_args(calls)

    env = run_args[run_args.index("-e") + 1]
    assert env.startswith("POSTGRES_PASSWORD=")
    password = env.split("=", 1)[1]
    assert password != "hermes", "hardcoded weak password"
    assert len(password) >= 20, "generated password must be unguessable"
    assert config["password"] == password, (
        "client config must use the generated password"
    )


def test_pgvector_password_differs_per_install(monkeypatch):
    _calls1, config1 = _run_ensure_pgvector(monkeypatch)
    _calls2, config2 = _run_ensure_pgvector(monkeypatch)
    assert config1["password"] != config2["password"]
