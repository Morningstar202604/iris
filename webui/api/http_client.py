"""Shared HTTP client plumbing for the Iris Web UI.

Consolidates the copy-pasted ``NoRedirectHandler`` that was previously
defined independently in five modules (auth_oidc, config, gateway_chat,
onboarding, runner_client) with identical behavior: refuse every redirect
so a 3xx can never forward ``Authorization``/Bearer headers to a different,
possibly attacker-controlled host.

Policy handlers that are used by exactly one module (IPv4-first, allowlist
redirect, same-origin redirect, pinned-CA, TTS no-redirect) intentionally
stay next to their only consumer.
"""

from __future__ import annotations

import urllib.request


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """urllib redirect handler that refuses to follow any redirect.

    ``redirect_request`` returning ``None`` makes urllib raise the original
    3xx as an ``HTTPError``, which callers can treat as "no redirect
    allowed" instead of silently leaking credentials to the new URL.
    """

    def redirect_request(self, *args, **kwargs):  # noqa: D102
        return None


def no_redirect_opener(*extra_handlers) -> urllib.request.OpenerDirector:
    """Build an opener that refuses redirects, plus any extra handlers."""
    return urllib.request.build_opener(NoRedirectHandler(), *extra_handlers)
