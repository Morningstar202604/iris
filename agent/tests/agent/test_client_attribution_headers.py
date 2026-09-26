"""Client-attribution contract for outbound provider headers.

The fork's identity is Iris: attribution headers must not be blanked out and
must not keep the old product token. The OAuth Claude Code path sets its own
user-agent downstream and is intentionally out of scope here.
"""

from __future__ import annotations

from agent import anthropic_adapter, auxiliary_client


def _assert_iris_attribution(headers: dict) -> None:
    assert headers.get("X-Title") == "Iris"
    assert headers.get("HTTP-Referer"), "HTTP-Referer must not be blank"
    ua = headers.get("User-Agent")
    if ua is not None:
        assert ua.startswith("IrisAgent/"), f"unexpected product token in {ua!r}"
        assert "Hermes" not in ua


def test_anthropic_attribution_headers_carry_iris_identity():
    _assert_iris_attribution(anthropic_adapter._attribution_headers())


def test_openrouter_base_headers_carry_iris_identity():
    _assert_iris_attribution(auxiliary_client._OR_HEADERS_BASE)


def test_ai_gateway_headers_carry_iris_identity():
    _assert_iris_attribution(auxiliary_client._AI_GATEWAY_HEADERS)


def test_oauth_system_replacements_have_unique_sources():
    sources = [old for old, _new in anthropic_adapter._OAUTH_SYSTEM_REPLACEMENTS]
    assert len(sources) == len(set(sources)), (
        "duplicate replacement rules are dead rules"
    )
