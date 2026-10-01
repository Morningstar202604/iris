# Windows / WSL auto-start

Iris WebUI runs well under WSL2, but native Windows login does not automatically start Linux user processes. This guide covers two supported options:

1. **WSL session startup** — simple and low-risk. WebUI starts the next time you open a WSL shell.
2. **Windows Task Scheduler** — true Windows logon startup. Windows invokes `wsl.exe`, which runs the WSL launch script.

Both paths use the same WSL launch script:

```text
scripts/wsl/iris_webui_autostart.sh
```

The script is safe to call repeatedly. It uses a lock file, checks the `/health` endpoint, checks a pid file, and writes logs before starting `start.sh --foreground` in the background. It does not hardcode a user path; by default it derives the repository root from its own location.

## Script settings

The WSL launcher supports these environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `IRIS_WEBUI_REPO` | repo containing the script | WebUI checkout to start |
| `IRIS_WEBUI_LOG_DIR` | `$HOME/.iris/webui/logs` | Autostart and WebUI logs |
| `IRIS_WEBUI_HOST` | `127.0.0.1` | Host passed through to `start.sh` / `bootstrap.py` |
| `IRIS_WEBUI_PORT` | `8787` | WebUI port and health-check port |
| `IRIS_WEBUI_HEALTH_URL` | `http://127.0.0.1:$IRIS_WEBUI_PORT/health` | URL used to decide whether WebUI is already running |
| `IRIS_WEBUI_PID_FILE` | `$IRIS_WEBUI_LOG_DIR/iris-webui.pid` | pid file used for duplicate prevention |
| `IRIS_WEBUI_REQUIRE_AGENT_PROCESS` | `0` | Optional: set to `1` only if your local setup requires a separate Iris process before WebUI starts |

Make the script executable once inside WSL:

```bash
cd /path/to/iris-webui
chmod +x scripts/wsl/iris_webui_autostart.sh
```

Run it manually to verify your paths and logs:

```bash
scripts/wsl/iris_webui_autostart.sh
curl -fsS http://127.0.0.1:8787/health
```

Logs are written to:

```text
$HOME/.iris/webui/logs/webui_autostart.log
$HOME/.iris/webui/logs/iris_webui.log
```

## Option 1: WSL session startup

This starts WebUI when your WSL login shell starts. It is the easiest option if you already open WSL during your day.

Add this to `~/.profile` or `~/.bashrc` inside WSL, adjusting the repo path:

```bash
if [ -x "$HOME/iris-webui/scripts/wsl/iris_webui_autostart.sh" ]; then
  IRIS_WEBUI_REPO="$HOME/iris-webui" \
    "$HOME/iris-webui/scripts/wsl/iris_webui_autostart.sh" >/dev/null 2>&1 &
fi
```

Open a new WSL terminal and check:

```bash
curl -fsS http://127.0.0.1:8787/health
```

If you open several WSL terminals, the launcher should still start only one WebUI process because the lock, health check, and pid file all converge on "already running".

## Option 2: Windows Task Scheduler startup

Use this if you want WebUI to start automatically at Windows logon even before you open a WSL terminal.

The helper PowerShell script is:

```text
scripts/windows/setup_webui_autostart.ps1
```

From Windows PowerShell, run it with the WSL path to the launch script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows\setup_webui_autostart.ps1 `
  -WslScriptPath "/home/your-user/iris-webui/scripts/wsl/iris_webui_autostart.sh" `
  -Distro "Ubuntu"
```

Notes:

- `-Distro` is optional. Omit it to use your default WSL distro.
- The default task name is `IrisWebUIAutoStart`; pass `-TaskName` if you need a different name.
- The script is idempotent: rerunning it updates the existing scheduled task instead of creating duplicates.
- The task runs as the current Windows user at logon with least privilege.
- Add `-WhatIf` to preview the scheduled task registration.
- Add `-RunNow` to start the task immediately after registration.
- Add `-SkipValidation` only if you need to register the task before the WSL path exists.

To inspect or remove the task later:

```powershell
Get-ScheduledTask -TaskName IrisWebUIAutoStart
Unregister-ScheduledTask -TaskName IrisWebUIAutoStart -Confirm:$false
```

## Troubleshooting

Check the WSL logs first:

```bash
tail -n 80 "$HOME/.iris/webui/logs/webui_autostart.log"
tail -n 80 "$HOME/.iris/webui/logs/iris_webui.log"
```

Common causes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Task exists but WebUI is not reachable | WSL script path is wrong for the selected distro | Re-run the PowerShell setup with the correct `-WslScriptPath` and `-Distro` |
| WebUI starts only after opening WSL | You used the WSL session startup option, not Task Scheduler | Install the Windows scheduled task |
| Multiple login events happen quickly | Normal Windows startup behavior | The WSL script should log `already running` and avoid duplicate processes |
| Health check fails but pid exists | WebUI is still booting or the port differs | Check `IRIS_WEBUI_PORT` and `iris_webui.log` |

If you want WSL2 systemd integration instead, see `docs/supervisor.md` for foreground process-supervisor guidance and adapt the Linux `systemd --user` pattern to your distro.
