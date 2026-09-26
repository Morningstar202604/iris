"""Request-log redaction: share tokens and credential query params.

Share URLs carry their access token in the path and some endpoints accept
tokens in the query string; the structured request log must never persist
either (log readers are not share recipients).
"""

from __future__ import annotations

from api.request_logging import redact_path_for_log


def test_share_page_token_is_redacted():
    assert redact_path_for_log("/share/s3cr3t-token-value") == "/share/<redacted>"


def test_share_api_token_is_redacted():
    assert (
        redact_path_for_log("/api/share/s3cr3t-token-value") == "/api/share/<redacted>"
    )


def test_sensitive_query_values_are_redacted_but_keys_kept():
    out = redact_path_for_log("/api/download?token=abc123&limit=50")
    assert "abc123" not in out
    assert "token=<redacted>" in out
    assert "limit=50" in out


def test_oauth_code_query_is_redacted():
    out = redact_path_for_log("/api/auth/callback?code=oauthcode&state=xyz")
    assert "oauthcode" not in out
    assert "code=<redacted>" in out


def test_ordinary_paths_pass_through_untouched():
    assert (
        redact_path_for_log("/api/sessions?limit=50&q=test")
        == "/api/sessions?limit=50&q=test"
    )


def test_empty_path_is_safe():
    assert redact_path_for_log("") == ""
