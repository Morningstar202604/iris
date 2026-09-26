"""DNS-rebinding defense for the CSRF origin gate.

The origin allowlist must anchor on the server's own hostnames, never on the
request's Host header: a rebind attacker's page sends ``Host: evil.com`` with
``Origin: http://evil.com``, and the two matching each other must NOT pass.
"""

from __future__ import annotations

from types import SimpleNamespace

import api.auth as auth
from api import routes


def _csrf_ok(headers: dict, monkeypatch) -> bool:
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    return routes._check_csrf(SimpleNamespace(headers=headers))


def test_rebinding_origin_matching_own_host_is_rejected(monkeypatch):
    assert not _csrf_ok({"Origin": "http://evil.com", "Host": "evil.com"}, monkeypatch)


def test_rebinding_with_matching_port_is_rejected(monkeypatch):
    assert not _csrf_ok(
        {"Origin": "http://evil.com:8787", "Host": "evil.com:8787"}, monkeypatch
    )


def test_loopback_same_origin_still_allowed(monkeypatch):
    assert _csrf_ok(
        {"Origin": "http://127.0.0.1:8787", "Host": "127.0.0.1:8787"}, monkeypatch
    )
    assert _csrf_ok(
        {"Origin": "http://localhost:8787", "Host": "localhost:8787"}, monkeypatch
    )


def test_local_service_hostnames_cover_loopback():
    names = routes._local_service_hostnames()
    assert {"localhost", "127.0.0.1", "::1"} <= names


def test_machine_hostname_origin_allowed(monkeypatch):
    hostname = routes._socket.gethostname().lower()
    assert hostname in routes._local_service_hostnames()
    assert _csrf_ok(
        {"Origin": f"http://{hostname}:8787", "Host": f"{hostname}:8787"}, monkeypatch
    )
