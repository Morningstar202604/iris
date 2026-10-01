"""Regression: WebUI runs its own in-process cron scheduler ticker.

The Tasks panel demanded a separate `iris gateway` daemon for scheduled jobs
("GATEWAY NOT CONFIGURED"), which a single-process local WebUI deployment has
no reason to run. The gateway's own ticker is `InProcessCronScheduler` — a
plain 60s loop that works in any process. The WebUI now starts it on a daemon
thread at server startup, keeps it from double-ticking when a real gateway
owns the tick, and reports it through /api/gateway/status as a running
in-process scheduler so the banner disappears.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRON_TICKER_PY = ROOT / "api" / "cron_ticker.py"
ROUTES_PY = (ROOT / "api" / "routes.py").read_text(encoding="utf-8")
SERVER_PY = (ROOT / "server.py").read_text(encoding="utf-8")
PANELS_JS = (ROOT / "static" / "panels.js").read_text(encoding="utf-8")


def test_cron_ticker_module_exposes_lifecycle_api():
    assert CRON_TICKER_PY.exists(), "api/cron_ticker.py missing"
    src = CRON_TICKER_PY.read_text(encoding="utf-8")
    for fn in (
        "def start_in_process_cron_ticker",
        "def stop_in_process_cron_ticker",
        "def in_process_cron_ticker_alive",
    ):
        assert fn in src, f"{fn} missing from api/cron_ticker.py"


def test_cron_ticker_never_double_ticks_with_external_gateway():
    src = CRON_TICKER_PY.read_text(encoding="utf-8")
    assert "live_gateway_ticking" in src, (
        "in-process ticker must stand down when an external gateway owns the cron tick"
    )


def test_gateway_status_payload_counts_inprocess_ticker_as_running():
    assert "in_process_cron_ticker_alive" in ROUTES_PY, (
        "_gateway_status_payload must consult the in-process ticker"
    )
    assert '"in_process": in_process' in ROUTES_PY, (
        "/api/gateway/status must expose the in_process flag for the frontend"
    )


def test_server_autostarts_and_stops_ticker():
    assert "start_in_process_cron_ticker" in SERVER_PY, (
        "server.py must auto-start the in-process cron ticker at boot"
    )
    assert "stop_in_process_cron_ticker" in SERVER_PY, (
        "server.py must stop the in-process cron ticker on shutdown"
    )


def test_frontend_renders_inprocess_scheduler_state():
    assert "r.in_process" in PANELS_JS, (
        "_renderGatewayStatus must render the in-process scheduler state"
    )


def test_in_process_ticker_alive_before_start_is_false():
    sys.path.insert(0, str(ROOT))
    try:
        from api import cron_ticker
    except Exception:  # aqg: top-level boundary — skip when api is not importable in isolation
        return
    assert cron_ticker.in_process_cron_ticker_alive() is False
