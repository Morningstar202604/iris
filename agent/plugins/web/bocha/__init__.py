"""博查 (BochaAI) 国产网页搜索插件 — bundled, auto-loaded."""
from __future__ import annotations
from plugins.web.bocha.provider import BochaWebSearchProvider


def register(ctx) -> None:
    ctx.register_web_search_provider(BochaWebSearchProvider())
