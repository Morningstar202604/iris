"""博查 (BochaAI) 国产 AI 网页搜索 — 中文搜索质量好、国内直连，无需翻墙。

Config: ``web.search_backend`` / ``web.backend: "bocha"``. Env: ``BOCHA_API_KEY``
（https://open.bochaai.com 免费申请，5 万次/月额度）。纯 HTTP（httpx），无额外依赖，
不需要 lazy_deps 白名单。仅搜索；正文提取可配 Firecrawl/Tavily 或本仓库内置提取。

API: POST https://api.bochaai.com/v1/web-search
Body: {"query": q, "count": N, "summary": True, "freshness": "noLimit"}
Resp: {"code":200, "data": {"webPages": {"value": [{name, url, snippet, summary}]}}}
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from plugins.web._common import BaseWebSearchProvider, provider_env, search_fail, search_ok, setup_schema, titled_rows

logger = logging.getLogger(__name__)

_BOCHA_ENDPOINT = "https://api.bochaai.com/v1/web-search"


class BochaWebSearchProvider(BaseWebSearchProvider):
    """Search-only BochaAI provider (国内 AI 搜索 API)."""

    NAME = "bocha"
    DISPLAY_NAME = "博查 AI 搜索 (Bocha)"
    KEY_ENV = "BOCHA_API_KEY"

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        api_key = provider_env("BOCHA_API_KEY")
        if not api_key:
            return search_fail("BOCHA_API_KEY is not set")
        try:
            resp = httpx.post(
                _BOCHA_ENDPOINT,
                json={"query": query, "count": max(1, min(int(limit), 50)), "summary": True, "freshness": "noLimit"},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Bocha HTTP error: %s", exc)
            return search_fail(f"Bocha returned HTTP {exc.response.status_code}")
        except httpx.RequestError as exc:
            logger.warning("Bocha request error: %s", exc)
            return search_fail(f"Could not reach BochaAI: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Bocha response parse error: %s", exc)
            return search_fail(f"Could not parse Bocha response as JSON: {exc}")

        raw = (((data.get("data") or {}).get("webPages") or {}).get("value")) or []
        web_results = titled_rows(raw[:limit], "snippet")
        logger.info("Bocha '%s': %d results (raw %d, limit %d)", query, len(web_results), len(raw), limit)
        return search_ok(web_results)

    def get_setup_schema(self) -> Dict[str, Any]:
        return setup_schema(
            "博查 AI 搜索 (Bocha)", "国产", "国内直连的中文 AI 搜索 — 免费额度 5 万次/月，搜索质量对标 AI 搜索产品。",
            "BOCHA_API_KEY", "博查 API key（open.bochaai.com 申请）", "https://open.bochaai.com",
        )
