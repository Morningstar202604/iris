"""Request output independent of agent/tool stdout capture."""

import os
import re
import threading


_SHARE_TOKEN_PATH_RE = re.compile(r"(^/(?:api/)?share/)[^/?#]+")
_SENSITIVE_QUERY_KEYS = frozenset({
    "access_token", "api_key", "apikey", "auth", "authorization", "client_secret",
    "code", "id_token", "key", "password", "refresh_token", "secret", "session",
    "sid", "sig", "signature", "token",
})


def redact_path_for_log(path: str) -> str:
    """Strip credential material from a request path before it hits the log.

    Share URLs carry their access token in the path (``/share/<token>``,
    ``/api/share/<token>``) and some endpoints accept tokens in the query
    string; log readers are not share recipients, so neither may be persisted.
    """
    if not path:
        return path
    redacted = _SHARE_TOKEN_PATH_RE.sub(r"\1<redacted>", path)
    base, sep, query = redacted.partition("?")
    if not sep:
        return redacted
    parts = []
    for pair in query.split("&"):
        key, eq, value = pair.partition("=")
        if eq and value and key.strip().lower() in _SENSITIVE_QUERY_KEYS:
            parts.append(f"{key}=<redacted>")
        else:
            parts.append(pair)
    return base + "?" + "&".join(parts)


# Import before agent code. Own the descriptor so replacing or closing Python's
# sys.stdout cannot capture access/error records intended for the service log.
try:
    _STREAM = os.fdopen(
        os.dup(1), "w", encoding="utf-8", errors="backslashreplace", buffering=1,
    )
except OSError:
    _STREAM = None
_LOCK = threading.Lock()


def emit_request_log(message: str) -> None:
    """Flush one complete record without letting a broken sink break HTTP."""
    try:
        if _STREAM is not None:
            with _LOCK:
                _STREAM.write(message + "\n")
                _STREAM.flush()
    except Exception:
        pass
