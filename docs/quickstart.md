# Quick Start

**English** · [简体中文](quickstart.zh-CN.md)

Iris is a **local-first** personal AI super-assistant: a full agent core with a modern
consumer-grade Web UI. This guide gets you running in 3 steps.

## 1. Clone & install

```bash
git clone https://gitcode.com/badhope/iris.git && cd iris

# Install the agent core (Hermes kernel + tools / plugins / memory / skills / cron)
cd agent && pip install -e . && cd ..
```

> Requires Python 3.11+. A virtualenv is recommended:
> ```bash
> python3 -m venv .venv && source .venv/bin/activate
> ```

## 2. Launch the Web UI

```bash
cd webui && python3 server.py
```

Open **http://127.0.0.1:8787** in your browser (change the port with `HERMES_WEBUI_PORT`).

**Key environment variables:**

| Variable | Purpose | Default |
|---|---|---|
| `HERMES_WEBUI_AGENT_DIR` | Agent source dir (this repo's `agent/`) | auto-detected |
| `HERMES_WEBUI_STATE_DIR` | Session / state data dir | `~/.hermes` |
| `HERMES_WEBUI_PORT` | Listen port | `8787` |
| `HERMES_WEBUI_PASSWORD` | Access password (optional) | empty = localhost, no password |

## 3. Connect a model

### Option A — built-in models
Open **Settings → Providers** and pick an available model.

### Option B — any OpenAI-compatible endpoint (recommended)
Edit `~/.hermes/config.yaml`:

```yaml
model:
  provider: custom:my-provider
  default: my-model
custom_providers:
  - name: my-provider
    base_url: https://your-endpoint/v1
    api_key: your-key
    models:
      - my-model
```

Save, then **restart the Web UI**.

### Image generation (optional)
Iris's drawing tool goes through the plugin mechanism. To point any OpenAI-compatible
endpoint at the image backend:

```yaml
plugins:
  enabled:
    - image_gen/openai
image_gen:
  provider: openai
  openai:
    provider: my-provider      # reuse the custom_providers endpoint + key
    model: my-image-model      # the endpoint's own image model name
```

### Unattended approvals (optional)
When tasks run unattended, script tools like `execute_code` need an approval policy:

```yaml
approvals:
  mode: smart        # smart = safe commands run automatically, dangerous ones ask
  timeout: 120
```

- `smart` — recommended; balances automation and safety
- `off` — run everything automatically (only if you fully trust the scripts)

## Self-healing watchdog (optional)

If the WebUI process is reclaimed by the environment (container / OOM), `ctl.sh` does
not restart it. Enable the watchdog for long-running stability:

```bash
cd webui
./watchdog.sh                 # poll /health every 10s, auto-restart on failure
./watchdog.sh --interval 30   # custom interval
./watchdog.sh --once          # single health check (scripts / CI)
```

## Next steps

- [`configuration.md`](configuration.md) — full configuration reference
- [`usage.md`](usage.md) — daily usage guide
- [`faq.md`](faq.md) — troubleshooting
