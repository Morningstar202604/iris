"""Startup bind guard: non-loopback without auth must fail closed.

Loopback-only serving stays warn-only, but binding 0.0.0.0/:: with no
authentication is only permitted after the operator explicitly acknowledged
the risk (auth_disabled_acknowledged). Unknown host values fail closed.
"""

from __future__ import annotations

import api.auth as auth


def _guard(host, *, auth_enabled, acknowledged, monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: auth_enabled)
    monkeypatch.setattr(
        auth, "load_settings", lambda: {"auth_disabled_acknowledged": acknowledged}
    )
    return auth.bind_security_error(host)


def test_non_loopback_without_auth_is_refused(monkeypatch):
    msg = _guard(
        "0.0.0.0", auth_enabled=False, acknowledged=False, monkeypatch=monkeypatch
    )
    assert msg is not None
    assert "0.0.0.0" in msg


def test_ipv6_wildcard_without_auth_is_refused(monkeypatch):
    assert (
        _guard("::", auth_enabled=False, acknowledged=False, monkeypatch=monkeypatch)
        is not None
    )


def test_unknown_host_fails_closed(monkeypatch):
    assert (
        _guard("", auth_enabled=False, acknowledged=False, monkeypatch=monkeypatch)
        is not None
    )


def test_acknowledged_risk_allows_bind(monkeypatch):
    assert (
        _guard(
            "0.0.0.0", auth_enabled=False, acknowledged=True, monkeypatch=monkeypatch
        )
        is None
    )


def test_configured_auth_allows_bind(monkeypatch):
    assert (
        _guard(
            "0.0.0.0", auth_enabled=True, acknowledged=False, monkeypatch=monkeypatch
        )
        is None
    )


def test_loopback_needs_no_acknowledgement(monkeypatch):
    for host in ("127.0.0.1", "::1", "localhost"):
        assert (
            _guard(
                host, auth_enabled=False, acknowledged=False, monkeypatch=monkeypatch
            )
            is None
        )
