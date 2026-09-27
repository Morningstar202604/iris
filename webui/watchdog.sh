#!/usr/bin/env bash
# Iris WebUI watchdog — self-healing supervisor.
#
# The WebUI daemon is normally started with `./ctl.sh start`. If the process is
# killed externally (container reclaim, OOM-killer, manual kill), ctl.sh does
# not auto-restart. This watchdog polls /health and restarts the daemon when it
# goes down, so a long-running Iris instance survives unexpected exits.
#
# Usage:
#   ./watchdog.sh                  # poll every 10s forever (Ctrl+C to stop)
#   ./watchdog.sh --interval 30    # poll every 30s
#   ./watchdog.sh --once           # single health check, exit 0/1
#   HERMES_WEBUI_PORT=8899 ./watchdog.sh   # non-default port
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERVAL=10
MODE="loop"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval) INTERVAL="$2"; shift 2 ;;
    --interval=*) INTERVAL="${1#*=}"; shift ;;
    --once) MODE="once"; shift ;;
    *) shift ;;
  esac
done

HOST="${HERMES_WEBUI_HOST:-127.0.0.1}"
PORT="${HERMES_WEBUI_PORT:-8787}"
LOG="${HERMES_WEBUI_WATCHDOG_LOG:-${HERMES_HOME:-${HOME}/.hermes}/webui.watchdog.log}"

# shellcheck source=scripts/lib/health_probe.sh
. "${REPO_ROOT}/scripts/lib/health_probe.sh"

is_healthy() {
  if hermes_webui_probe_health "${HOST}" "${PORT}" "/health" 2 >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

log() { echo "[$(date '+%F %T')] $*" | tee -a "${LOG}"; }

check_once() {
  if is_healthy; then
    return 0
  fi
  log "WebUI unhealthy/down at ${HOST}:${PORT} — restarting via ctl.sh"
  if ! (cd "${REPO_ROOT}" && ./ctl.sh restart >/dev/null 2>&1); then
    # Fall back to a direct bootstrap start when ctl.sh state is stale.
    log "ctl.sh restart failed — trying direct start"
    (cd "${REPO_ROOT}" && ./start.sh --no-browser >/dev/null 2>&1) || true
  fi
  # Wait for the new instance to answer /health.
  for _ in $(seq 1 30); do
    sleep 2
    if is_healthy; then
      log "WebUI recovered"
      return 0
    fi
  done
  log "WebUI still down after restart"
  return 1
}

if [[ "${MODE}" == "once" ]]; then
  if is_healthy; then
    exit 0
  fi
  check_once
  exit $?
fi

log "watchdog started (interval ${INTERVAL}s, target ${HOST}:${PORT})"
while true; do
  sleep "${INTERVAL}"
  if ! is_healthy; then
    check_once || true
  fi
done
