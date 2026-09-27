# Configuration Reference

**English** · [简体中文](configuration.zh-CN.md)

Iris runtime configuration lives in `~/.hermes/config.yaml` (auto-created on first run).
This reference covers the blocks most relevant to daily use. All settings are also
editable in the Web UI **Settings** panel; the config file takes precedence.

## model — main model

```yaml
model:
  provider: custom:agnes      # provider ID
  default: agnes-3.0-flash    # default model
  base_url: https://your-endpoint/v1
```

- `context_length` (optional): declare the model's context window explicitly to skip
  probing latency. Example: `context_length: 128000`. When unset, Iris auto-detects
  (custom endpoints fall back quickly to a default).

## custom_providers — custom providers

```yaml
custom_providers:
  - name: agnes                    # group name shown in the model picker
    base_url: https://your-endpoint/v1
    api_key: your-key
    models:
      - model-a                    # models this endpoint offers
      - model-b
```

- Once added, the endpoint and its models appear in the Web UI model dropdown.
- Instead of a literal key you may set `key_env: MY_API_KEY_ENV` to read from an
  environment variable.

## plugins — plugins

```yaml
plugins:
  enabled:
    - web-defuddle          # web page text extraction
    - web-knowledge-base    # knowledge-base search
    - image_gen/openai      # image backend (OpenAI-compatible endpoint)
  disabled: []
```

Plugins are referenced as `type/name` (e.g. `image_gen/openai`). `plugins.enabled`
is a whitelist — unlisted plugins are not loaded.

## image_gen — image generation

```yaml
image_gen:
  provider: openai          # image backend
  openai:
    provider: agnes         # reuse a custom_providers endpoint / key
    model: your-image-model # the endpoint's own image model name (passed through)
```

- `image_gen.openai.provider` points at an entry in `custom_providers`, inheriting its
  `base_url` and `api_key`.
- Without this block the `image_generate` tool is hidden from the tool list.

## approvals — approvals

```yaml
approvals:
  mode: smart               # manual | smart | off
  timeout: 120              # seconds to wait for a human approval
```

| Mode | Behavior |
|---|---|
| `manual` | Every script-like tool waits for approval (**unattended tasks time out**) |
| `smart` | Safe commands run automatically; dangerous ones ask (**recommended**) |
| `off` | Everything runs automatically (only if you trust the scripts) |

When running long tasks unattended via Web UI / API, use `smart` — otherwise tools
such as `execute_code` wait for approval until timeout.

## Prompts & personalization

- **Persona**: Web UI **Settings → Preferences**, or the `personalities` block.
- **Preset prompts**: the preset dropdown above the composer stores frequent
  instruction templates.

## Environment variables

| Variable | Purpose |
|---|---|
| `HERMES_WEBUI_AGENT_DIR` | Agent source directory |
| `HERMES_WEBUI_STATE_DIR` | State / session data directory |
| `HERMES_WEBUI_PORT` | Web UI port (default 8787) |
| `HERMES_WEBUI_PASSWORD` | Access password |
| `HERMES_PLUGINS_DEBUG` | `1` to print plugin-load debug logs |

## Applying changes

After editing `config.yaml`, **restart the Web UI**:

```bash
# stop the old process, then
cd webui && python3 server.py
```

> If you see `agent_runtime_stale`, it means agent source or config changed while the
> server was running — restart the Web UI to recover. This is a safety guard, not a bug.
