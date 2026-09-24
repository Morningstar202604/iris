"""
Plugin discovery and static serving for Hermes Web UI.

Scans ~/.hermes/plugins/<name>/dashboard/ for manifest.json files,
matching the official Hermes dashboard plugin format.

Each plugin may have:
  dashboard/
    manifest.json   -- tab definition and entry point
    dist/
      index.js      -- plugin JS bundle (IIFE)
      style.css     -- optional plugin stylesheet
    plugin_api.py   -- optional backend API (not used in WebUI MVP)
"""
import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Valid dashboard-plugin name: a safe slug (it becomes a URL path component and
# a settings key). Lowercase alnum + - / _, 1-64 chars, must start with a letter.
_VALID_PLUGIN_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")

# Valid tab.path: a clean same-origin absolute path. Must start with a single
# '/' (NOT '//' — a leading '//' is a protocol-relative URL that would resolve
# to a remote origin when assigned to iframe.src), then only safe path chars —
# no quotes, whitespace, control chars, query ('?') or fragment ('#').
_VALID_PLUGIN_TAB_PATH = re.compile(r"^/(?!/)[A-Za-z0-9._~/-]{0,255}$")

# plugin_name -> manifest dict (as loaded from manifest.json)
PLUGIN_MANIFESTS: dict[str, dict] = {}

# plugin_name -> resolved static root dir
_PLUGIN_STATIC_ROOTS: dict[str, Path] = {}


def _get_plugin_base() -> Path:
    return Path(os.environ.get("HERMES_WEBUI_PLUGINS_DIR", str(Path.home() / ".hermes" / "plugins")))


def load_plugins() -> None:
    """Scan plugin directories and load manifest.json for each dashboard plugin."""
    plugin_base = _get_plugin_base()
    if not plugin_base.is_dir():
        logger.debug("No plugins directory at %s", plugin_base)
        return

    for entry in sorted(plugin_base.iterdir()):
        if not entry.is_dir():
            continue
        manifest_path = entry / "dashboard" / "manifest.json"
        if not manifest_path.is_file():
            continue

        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            logger.exception("Failed to parse manifest for plugin %s", entry.name)
            continue

        name = manifest.get("name") or entry.name

        # Validate the plugin name: it becomes a URL path component
        # (/dashboard-plugins/<name>/...) and a settings key. Restrict to a safe
        # slug so a manifest like name:"../foo" can't make the URL-space ambiguous.
        if not _VALID_PLUGIN_NAME.match(str(name)):
            logger.warning("Skipping plugin with invalid name %r (must match %s)", name, _VALID_PLUGIN_NAME.pattern)
            continue

        tab = manifest.get("tab", {})
        tab_path = tab.get("path", f"/{name}")

        # Validate tab.path: it's a same-origin route the plugin page is served
        # at AND a value passed into client-side navigation. Require a clean
        # absolute path — no quotes/control chars/query/fragment — so a hostile
        # manifest can't shadow odd routes or inject via the path.
        if not _VALID_PLUGIN_TAB_PATH.match(str(tab_path)):
            logger.warning("Skipping plugin %s with invalid tab.path %r (must match %s)", name, tab_path, _VALID_PLUGIN_TAB_PATH.pattern)
            continue

        if name in PLUGIN_MANIFESTS:
            logger.warning("Duplicate plugin name skipped: %s (already loaded)", name)
            continue
        if tab_path in (m.get("tab", {}).get("path") for m in PLUGIN_MANIFESTS.values()):
            logger.warning("Plugin %s tab.path %r conflicts with another plugin; skipped", name, tab_path)
            continue

        PLUGIN_MANIFESTS[name] = manifest
        logger.info("Loaded dashboard plugin: %s (label=%s)", name, manifest.get("label", ""))

        # Pre-compute static root for fast serving (points to dashboard/)
        dashboard_dir = entry / "dashboard"
        if dashboard_dir.is_dir():
            _PLUGIN_STATIC_ROOTS[name] = dashboard_dir.resolve()


def serve_plugin_static(plugin_name: str, rel_path: str) -> tuple[bytes, str] | None:
    """
    Serve a built static asset from a plugin's dashboard/dist/ (or static/) dir.

    Returns (file_bytes, content_type) on success, None on not found.

    Security: _PLUGIN_STATIC_ROOTS points at the plugin's whole dashboard/ dir
    (the page route needs that), but the asset route must NOT expose plugin
    source/config — e.g. dashboard/plugin_api.py, manifest.json, .env. So we
    constrain served files to the built-asset subtrees (dist/ or static/), reject
    dotfiles, and require a known static extension.
    """
    root = _PLUGIN_STATIC_ROOTS.get(plugin_name)
    if not root:
        return None

    safe = (root / rel_path.lstrip("/")).resolve()
    try:
        safe.relative_to(root)
    except ValueError:
        return None  # path traversal attempt

    # Only built-asset subtrees are servable (not the dashboard root itself,
    # which holds plugin_api.py / manifest.json / config).
    rel = safe.relative_to(root)
    if not rel.parts or rel.parts[0] not in ("dist", "static"):
        return None
    # No dotfiles (.env, .git, etc.) anywhere in the path.
    if any(part.startswith(".") for part in rel.parts):
        return None

    if not safe.is_file():
        return None

    # Allowlist of static asset extensions — refuse source/config (.py, .json,
    # .toml, .env, .sh, ...) even if somehow placed under dist/.
    ext = os.path.splitext(rel_path.lower())[1]
    _STATIC_EXTS = {
        ".js", ".css", ".html", ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".ico", ".webp", ".woff", ".woff2", ".ttf", ".otf", ".map", ".txt",
    }
    if ext not in _STATIC_EXTS:
        return None

    data = safe.read_bytes()
    content_type = {
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }.get(ext, "application/octet-stream")

    return data, content_type


def get_plugin_metadata() -> list[dict]:
    """
    Return a list of plugin metadata suitable for the Settings → Plugins tab.
    Each entry includes name, key, version, description, and tab info for linking.

    Per-plugin enabled state is stored in settings.json under `dashboard_plugins`.
    A plugin is enabled only if the user has explicitly toggled it on (default off).
    """
    from api.config import load_settings

    plugin_settings = load_settings().get("dashboard_plugins", {})
    plugins = []
    for name, manifest in sorted(PLUGIN_MANIFESTS.items()):
        tab = manifest.get("tab", {})
        path = tab.get("path", f"/{name}")
        plugins.append({
            "name": manifest.get("label") or manifest.get("name") or name,
            "key": name,
            "version": manifest.get("version", "0.0.0"),
            "description": manifest.get("description", ""),
            "tab": {
                "path": path,
                "label": tab.get("label") or manifest.get("label") or name,
            },
            "enabled": bool(plugin_settings.get(name, False)),
            "hooks": [],
        })
    return plugins


# ────────────────────────────────────────────────────────────────────────────
# Iris: 插件安装 / 卸载 / 启停管理（复用 hermes CLI，含安全扫描与依赖安装）
# ────────────────────────────────────────────────────────────────────────────
import shutil
import subprocess
import sys

_PLUGIN_CLI_TIMEOUT = 300  # 安装含依赖解析，给足超时


def _hermes_cli_command() -> list[str]:
    """Locate the ``hermes`` executable; fall back to ``python -m hermes_cli.main``."""
    exe = shutil.which("hermes")
    if exe:
        return [exe]
    return [sys.executable, "-m", "hermes_cli.main"]


def _hermes_cli_env() -> dict:
    """子进程环境：`-m` 回退时把 hermes-agent 目录注入 PYTHONPATH。

    WebUI 与 hermes-agent 是独立仓库；当前进程的 sys.path 注入（api.config
    启动时 append）不会被子进程继承，必须通过 PYTHONPATH 显式传递，
    否则 `python -m hermes_cli.main` 在子进程里 ModuleNotFoundError。
    系统已安装 `hermes` 命令时无需注入（环境本来就能跑）。
    """
    env = dict(os.environ)
    if shutil.which("hermes"):
        return env
    try:
        from api.config import _AGENT_DIR
    except Exception:
        return env
    if not _AGENT_DIR:
        return env
    agent = str(_AGENT_DIR)
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = agent + (os.pathsep + current if current else "")
    return env


def _run_plugin_cli(args: list[str], timeout: int = _PLUGIN_CLI_TIMEOUT) -> dict:
    """Run ``hermes plugins <args>`` and return {ok, output, error, exit_code}.

    失败时不抛异常——把 hermes CLI 的 stderr 原样回传，前端可展示具体原因。
    """
    try:
        proc = subprocess.run(
            _hermes_cli_command() + ["plugins"] + args,
            capture_output=True, text=True, timeout=timeout,
            env=_hermes_cli_env(),
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "exit_code": proc.returncode,
            "output": stdout or stderr or ("" if ok else "hermes plugins 命令失败"),
            "error": stderr if not ok else "",
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit_code": -1, "output": "", "error": "hermes plugins 命令超时（安装依赖可能较慢，请重试）"}
    except FileNotFoundError:
        return {"ok": False, "exit_code": -1, "output": "", "error": "未找到 hermes 可执行文件（hermes-agent 未安装）"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "exit_code": -1, "output": "", "error": f"插件命令执行失败: {exc}"}


def install_plugin(identifier: str) -> dict:
    """安装并启用一个插件（catalog 条目名 / Git URL / owner/repo）。"""
    if not isinstance(identifier, str) or not identifier.strip():
        return {"ok": False, "exit_code": -1, "output": "", "error": "缺少插件标识符"}
    return _run_plugin_cli(["install", identifier.strip(), "--enable"])


def remove_plugin(name: str) -> dict:
    """卸载一个已安装插件。"""
    if not isinstance(name, str) or not name.strip():
        return {"ok": False, "exit_code": -1, "output": "", "error": "缺少插件名"}
    return _run_plugin_cli(["remove", name.strip()])


def toggle_plugin(name: str, enable: bool) -> dict:
    """启用 / 停用一个已安装插件。"""
    if not isinstance(name, str) or not name.strip():
        return {"ok": False, "exit_code": -1, "output": "", "error": "缺少插件名"}
    action = "enable" if enable else "disable"
    return _run_plugin_cli([action, name.strip()])


def catalog_plugins(term: str = "") -> dict:
    """列出可安装的官方插件目录（含描述），支持关键字过滤。"""
    # `plugins browse` 不支持 --json；`plugins search --json`（空 term=列出整个目录）
    args = ["search", term.strip(), "--json"]
    result = _run_plugin_cli(args, timeout=60)
    if not result["ok"]:
        return result
    try:
        import json as _json
        data = _json.loads(result["output"])
    except Exception:  # noqa: BLE001
        return {"ok": True, "exit_code": 0, "output": result["output"], "error": "", "raw": True}
    return {"ok": True, "exit_code": 0, "output": data, "error": "", "raw": False}
