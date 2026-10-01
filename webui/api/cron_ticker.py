"""In-process cron scheduler ticker for single-process WebUI deployments.

The Tasks panel used to demand a separate ``iris gateway`` daemon for
scheduled jobs. A single-process local WebUI has no reason to run one: the
gateway's own ticker is ``InProcessCronScheduler`` — a plain 60s loop that
works in any process. This module starts it on a supervised daemon thread at
server startup, and keeps it from double-ticking when a real external gateway
process owns the cron tick (stand-down at start plus a watchdog that yields
if a gateway appears later).
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_stop_event: threading.Event | None = None
_ticker_thread: threading.Thread | None = None
_watchdog_thread: threading.Thread | None = None
_last_start_error: str | "" = ""

TICK_INTERVAL_S = 60
_WATCHDOG_INTERVAL_S = 120


def _external_gateway_is_ticking() -> bool:
    """True when a live external gateway process owns the cron tick."""
    try:
        from cron.scheduler_ownership import live_gateway_ticking

        return live_gateway_ticking() is not None
    except Exception:  # aqg: top-level boundary — optional agent module; never block status
        return False


def _install_profile_isolation() -> None:
    """Give auto-fired jobs the same IRIS_HOME isolation as manual runs."""
    try:
        from api.profiles import install_cron_scheduler_profile_isolation

        install_cron_scheduler_profile_isolation()
    except Exception:  # aqg: top-level boundary — optional patch; tick without isolation beats no tick
        logger.debug(
            "cron scheduler profile isolation unavailable", exc_info=True
        )


def _watchdog_entry() -> None:
    """Yield the in-process ticker if an external gateway takes over the tick."""
    assert _stop_event is not None
    while not _stop_event.wait(_WATCHDOG_INTERVAL_S):
        try:
            if _external_gateway_is_ticking():
                logger.info(
                    "External gateway now owns the cron tick; stopping the "
                    "WebUI in-process cron scheduler to avoid double dispatch"
                )
                _stop_event.set()
                return
        except Exception:  # aqg: top-level boundary — probe failure must not kill the watchdog
            logger.debug("cron ownership watchdog probe failed", exc_info=True)


def _ticker_entry(stop_event: threading.Event) -> None:
    try:
        from cron.scheduler_provider import InProcessCronScheduler
    except Exception:  # aqg: top-level boundary — no agent checkout means the gateway stays the only option
        global _last_start_error
        _last_start_error = "cron scheduler provider unavailable in this install"
        logger.warning(
            "In-process cron scheduler unavailable; scheduled jobs still need "
            "the gateway daemon in this deployment"
        )
        return
    scheduler = InProcessCronScheduler()
    scheduler.start(stop_event, interval=TICK_INTERVAL_S)


def start_in_process_cron_ticker() -> bool:
    """Start the in-process cron ticker unless an external gateway owns it."""
    global _stop_event, _ticker_thread, _watchdog_thread, _last_start_error
    with _lock:
        if _ticker_thread is not None and _ticker_thread.is_alive():
            return True
        if _external_gateway_is_ticking():
            logger.info(
                "External gateway is ticking cron; in-process ticker stays off"
            )
            _last_start_error = ""
            return False
        _last_start_error = ""
        _install_profile_isolation()
        _stop_event = threading.Event()
        _ticker_thread = threading.Thread(
            target=_ticker_entry,
            args=(_stop_event,),
            daemon=True,
            name="webui-cron-ticker",
        )
        _watchdog_thread = threading.Thread(
            target=_watchdog_entry,
            daemon=True,
            name="webui-cron-watchdog",
        )
        _ticker_thread.start()
        _watchdog_thread.start()
        logger.info(
            "In-process cron scheduler started (interval=%ds)", TICK_INTERVAL_S
        )
        return True


def stop_in_process_cron_ticker() -> None:
    """Request shutdown; daemon threads exit on their own."""
    global _stop_event, _ticker_thread, _watchdog_thread
    with _lock:
        if _stop_event is not None:
            _stop_event.set()
        _ticker_thread = None
        _watchdog_thread = None


def in_process_cron_ticker_alive() -> bool:
    thread = _ticker_thread
    return bool(thread is not None and thread.is_alive())
