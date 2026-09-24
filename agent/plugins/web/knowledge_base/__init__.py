"""Iris 个人文档知识库插件 — bundled, auto-loaded.

文档索引由 WebUI（server）写入 ``$HERMES_HOME/knowledge.db``；
本插件注册 ``kb_search`` 工具，让 agent 在对话中自行检索知识库。
零第三方依赖：SQLite FTS5 + trigram/cjk 中文分词。
"""

from __future__ import annotations

import json

from .tools import _search


def register(ctx) -> None:
    """注册 kb_search 工具（backend 插件在 register() 内直接注册工具）。"""
    ctx.register_tool(
        name="kb_search",
        toolset="knowledge_base",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "要在个人知识库中检索的关键词或问题"},
                "top_k": {"type": "integer", "description": "返回的匹配片段数量，默认 4"},
            },
            "required": ["query"],
        },
        handler=lambda args: json.dumps(_search(args.get("query", ""), args.get("top_k", 4)), ensure_ascii=False),
        description=(
            "Search the user's personal knowledge base (documents they uploaded "
            "via the Iris knowledge base) and return matching excerpts with "
            "document titles. Use when the user asks about content in their "
            "uploaded documents or personal notes."
        ),
        emoji="📚",
    )
