"""事件循环强化：装了 uvloop 就用 libuv 后端（吞吐 2-4x），否则静默回退 stdlib。

uvloop 是 [uvloop] extra 的可选依赖（pyproject 已声明），但 Python 不会自动启用它——
必须显式 ``uvloop.install()``。此前整库从未调用，导致安装后等于没装。本模块提供
统一入口，gateway / CLI-TUI 两个主进程各在自己的 ``main()`` 最前面调用一次即可
（必须在任何事件循环创建之前）。import 失败或平台不兼容时静默降级，绝不影响启动。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def install_uvloop_if_available() -> bool:
    """Best-effort 启用 uvloop。返回 True=已启用；False=回退 stdlib asyncio。"""
    try:
        import uvloop  # type: ignore[import-not-found]
    except Exception:
        # uvloop 未安装（lean 安装）或当前平台无可用 wheel —— 正常降级路径。
        return False
    try:
        uvloop.install()
        logger.debug("uvloop installed: libuv event loop active")
        return True
    except Exception as exc:  # noqa: BLE001
        # install() 理论上极少失败（已在运行的 loop/策略冲突）；降级不报错。
        logger.debug("uvloop install skipped (%s); falling back to stdlib asyncio", exc)
        return False
