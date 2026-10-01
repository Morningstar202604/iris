# Configuration Reference

**English** · [简体中文](configuration.zh-CN.md)

Iris runtime configuration lives in `$IRIS_HOME/config.yaml` (auto-created on first run).
By default `$IRIS_HOME` is `~/.iris` on Linux/macOS and `%LOCALAPPDATA%\iris` on Windows.
This reference covers the blocks most relevant to daily use. All settings are also
editable in the Web UI **Settings** panel; the config file takes precedence.

> Canonical, fully-annotated source of truth: `agent/cli-config.yaml.example`.
> Defaults listed below are extracted from that file and
> `agent/iris_cli/config_defaults.py` — do not invent keys.

## Files on disk

```
~/.iris/
├── config.yaml          # runtime config (this file)
├── .env                 # API keys & secret env vars (chmod 600)
├── auth.json            # OAuth session tokens (Codex, Nous, …)
├── active_profile       # name of the sticky-active named profile
├── state.db             # sessions, messages, tool calls, FTS5 search index
├── SOUL.md              # agent identity / system prompt
├── cron/  sessions/  logs/  memories/  pairing/  hooks/
├── image_cache/  audio_cache/  skills/
└── profiles/<name>/     # per-profile homes (named profiles only)
```

- **Profiles:** the default profile *is* `~/.iris`. Named profiles live under
  `~/.iris/profiles/<name>/` and each carries its own `config.yaml`, `.env`,
  `state.db`, etc. Switch with `iris profile use <name>`; the active name is
  written to `~/.iris/active_profile`.
- Edit in place, or use `iris config set <section.key> <value>`.

## model — main model

```yaml
model:
  default: "anthropic/claude-opus-4.6"  # default model ("model:" is an accepted alias)
  provider: "auto"                       # provider ID (see list below)
  base_url: "https://openrouter.ai/api/v1"
  # api_key: "your-key-here"             # optional; falls back to provider env var
  # streaming: true                      # false = force non-streaming for the whole session
  # context_length: 131072              # total context window; leave unset to auto-detect
```

| `provider` value | Meaning | Required credential |
|---|---|---|
| `auto` | Auto-detect from available credentials (**default**) | — |
| `openrouter` | OpenRouter | `OPENROUTER_API_KEY` or `OPENAI_API_KEY` |
| `nous` / `nous-api` | Nous Portal (OAuth / API key) | `iris auth add nous` / `NOUS_API_KEY` |
| `anthropic` | Direct Anthropic API | `ANTHROPIC_API_KEY` |
| `openai-codex` | OpenAI Codex (OAuth) | `iris auth add openai-codex` |
| `copilot` | GitHub Copilot / GitHub Models | `GITHUB_TOKEN` |
| `gemini` | Google AI Studio direct | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| `zai` | z.ai / ZhipuAI GLM | `GLM_API_KEY` |
| `kimi-coding` | Kimi / Moonshot | `KIMI_API_KEY` |
| `minimax` / `minimax-cn` | MiniMax global / China | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` |
| `huggingface` | Hugging Face Inference | `HF_TOKEN` |
| `nvidia` | NVIDIA NIM | `NVIDIA_API_KEY` |
| `xiaomi` | Xiaomi MiMo | `XIAOMI_API_KEY` |
| `arcee` | Arcee AI Trinity | `ARCEEAI_API_KEY` |
| `ollama-cloud` | Ollama Cloud | `OLLAMA_API_KEY` |
| `deepinfra` | DeepInfra | `DEEPINFRA_API_KEY` |
| `kilocode` | KiloCode gateway | `KILOCODE_API_KEY` |
| `ai-gateway` | Vercel AI Gateway | `AI_GATEWAY_API_KEY` |
| `azure-foundry` | Azure OpenAI / Foundry | API key or Entra ID |
| `lmstudio` | LM Studio local server | optional `LM_API_KEY` (default `http://127.0.0.1:1234/v1`) |
| `custom` | Any OpenAI-compatible endpoint (set `base_url`) | `base_url` + key |

`ollama`, `vllm`, `llamacpp` are aliases that all map to `custom`.

- `context_length` (optional): total context window (input + output). Set manually
  only when auto-detection is wrong (local server with custom `num_ctx`, or a proxy
  that does not expose `/v1/models`).
- `ollama_num_ctx`: Ollama-only `num_ctx` sent on every request; an explicit value is
  sent as-is (never capped).
- `default_headers` / `extra_headers`: extra HTTP headers on every OpenAI-wire
  request (useful to override the SDK `User-Agent` behind a gateway/WAF).
  `extra_headers` wins when both are set.

### providers: — named per-provider overrides

```yaml
providers:
  my-proxy:
    base_url: "https://llm.internal.example.com/v1"
    api_key: "${MY_PROXY_API_KEY}"   # or key_env: MY_PROXY_API_KEY
    extra_headers:
      X-Client-Name: "iris-agent"
    request_timeout_seconds: 300     # per-provider request timeout
    stale_timeout_seconds: 900       # non-stream stale-call detector
    models:                          # per-model exceptions
      claude-opus-4.6:
        timeout_seconds: 600
```

- `key_cmd`: a command that **prints** a fresh bearer token per request (cached
  until near expiry) — for short-lived SSO/OIDC/IAM tokens. Precedence: `--api-key`
  > `key_cmd` > inline `api_key` / `key_env`.
- `extra_body`: dict merged into every request routed to this provider (e.g. a
  gateway's own `service_tier: priority`).
- `session_affinity_header`: name of a header carrying the conversation id on every
  request, for session-aware proxies.

### custom_providers — endpoint groups shown in the model picker

```yaml
custom_providers:
  - name: agnes                    # group name shown in the model picker
    base_url: https://your-endpoint/v1
    api_key: your-key              # OR: key_env: MY_API_KEY_ENV
    models:
      - model-a
      - model-b
```

- Once added, the endpoint and its models appear in the Web UI model dropdown.
- `key_env: MY_API_KEY_ENV` reads the key from an environment variable instead of
  writing it in the file.

### fallback_providers — failover chain

When the primary provider errors with a transient outage (5xx, overloaded/529,
connect/read timeout), Iris walks this chain before giving up.

```yaml
fallback_providers:
  - provider: "openrouter"
    model: "deepseek/deepseek-chat"
    # base_url: "https://..."      # optional, for a custom endpoint
    # api_key: "sk-..."            # optional; else key_env:
```

- Each entry needs `provider` + `model`. Legacy `fallback_model` (a single dict) is
  still merged in after `fallback_providers`.
- An explicit `[]` disables fallback.

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
Other keys (all optional): `plugins.hook_callback_timeout` (default `30`s),
`plugins.load_timeout_seconds` (default `10`s).

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
- Other provider plugins (`deepinfra`, …) read their own `image_gen.<name>` block;
  `deepinfra` discovers models live from the catalog.

## approvals — approvals

```yaml
approvals:
  mode: smart               # manual | smart | off
  timeout: 300              # seconds to wait for a human approval (default)
  cron_mode: deny            # deny | approve — cron jobs hitting a dangerous command
  single_query_mode: deny    # deny | approve — `-q` one-shot sessions
  unattended_mode: deny      # deny | approve — webhook / api_server surfaces
```

| Mode | Behavior |
|---|---|
| `manual` | Every script-like tool waits for approval (**unattended tasks time out**) |
| `smart` | Safe commands auto-approved by a guardian LLM; dangerous ones ask (**recommended**) |
| `off` | Everything runs automatically (only if you trust the scripts) |

When running long tasks unattended via Web UI / API, use `smart` — otherwise tools
such as `execute_code` wait for approval until `timeout` elapses. Extra keys:
`approvals.deny` (fnmatch globs blocked even under `off`),
`approvals.smart_policy` (extra guardian rules),
`approvals.denial_breaker_threshold` (default `3`).

## terminal — command execution backend

```yaml
terminal:
  backend: "local"          # local | ssh | docker | singularity | modal | daytona
  cwd: "."                  # "." = launch dir (local); path inside container/remote otherwise
  timeout: 180              # per-command timeout (seconds)
  lifetime_seconds: 300     # shell/container max idle lifetime
  home_mode: "auto"         # auto | real | profile — HOME policy for tool subprocesses
  docker_mount_cwd_to_workspace: false   # SECURITY: opt-in
```

Container backends (`docker`, `singularity`, `modal`, `daytona`) also accept:
`container_cpu` (default `1`), `container_memory` (default `5120` MB),
`container_disk` (default `51200` MB), `container_persistent` (default `true`),
and backend-specific keys (`docker_image`, `ssh_host`/`ssh_user`/`ssh_port`/`ssh_key`,
`singularity_image`, `modal_image`, `daytona_image`, …). See
`agent/cli-config.yaml.example` for the full per-backend reference.

## agent — agent loop behavior

```yaml
agent:
  max_turns: 500                  # max tool-calling iterations per conversation
  verbose: false                  # verbose logging
  reasoning_effort: "medium"      # xhigh | high | medium | low | minimal | none
  reasoning_overrides: {}         # per-model effort overrides
  service_tier: ""                # ""/normal | fast | auto | cold (first-party fast tier)
  fast_auto_seconds: 60
  personalities: {}               # custom / override built-in personas
  api_max_retries: 3              # Iris-level retries on API errors
  auto_recovery_cycles: 5         # extra jittered retry cycles on transient outages
```

## compression — context auto-compaction

```yaml
compression:
  enabled: true
  threshold: 0.50                 # trigger at this fraction of context_length
  threshold_tokens: 256000        # absolute token cap on the trigger
  target_ratio: 0.20              # fraction of threshold kept as recent tail
  protect_last_n: 20              # recent messages always preserved
  protect_first_n: 3              # head messages always preserved
  max_attempts: 3                 # compression retry rounds before giving up
  checkpoint_required: false       # fail closed unless a memory provider checkpoints
```

Small-context models (< 512K) floor the trigger at `0.75` (raise-only).

## memory — persistent memory

```yaml
memory:
  memory_enabled: true             # agent notes (MEMORY.md)
  user_profile_enabled: true       # user profile (USER.md)
  memory_char_limit: 2200          # ~800 tokens
  user_char_limit: 1375            # ~500 tokens
  nudge_interval: 10              # remind agent to save memories every N turns (0 = off)
```

## skills, toolsets & MCP

- **skills:** `skills.creation_nudge_interval` (default `15`), `skills.external_dirs`
  (read-only extra skill directories).
- **platform_toolsets:** per-platform tool whitelist. Default presets:
  `cli: [iris-cli]`, `telegram/discord/whatsapp/slack/signal/…: [iris-<platform>]`.
  Compose from individual toolsets: `web, search, terminal, file, browser, vision,
  image_gen, skills, skills_hub, todo, tts, cronjob`. Run `iris chat --list-toolsets`.
  The top-level `toolsets` key is **deprecated** and ignored.
- **mcp_servers:** named stdio/HTTP MCP servers:
  ```yaml
  mcp_servers:
    filesystem:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
      timeout: 120            # per-tool-call timeout
      connect_timeout: 60      # initial connection timeout
      lazy: false              # spawn on first tool call only
  ```

## display — CLI / gateway rendering

```yaml
display:
  compact: false                  # single-line banner
  tool_progress: all              # off | new | all | verbose | log
  streaming: true                 # stream tokens to the terminal
  show_reasoning: true            # show the thinking box
  interim_assistant_messages: true
  long_running_notifications: true
  busy_input_mode: interrupt      # interrupt | queue | steer
  bell_on_complete: false
  skin: default                   # default | mono | slate | daylight | …
```

## stt / tts — voice

```yaml
stt:
  enabled: true                   # transcribe voice messages on messaging platforms
  # provider: local               # local | groq | openai | mistral | deepinfra (auto if unset)
  language: "en"                  # global hint; "" = auto-detect
  local:
    model: "base"                 # tiny | base | small | medium | large-v3 | turbo
  openai:
    model: "whisper-1"
    timeout: 60
```

TTS defaults to Edge TTS (free). Set `tts.provider` to `gemini`, `openai`, `xai`,
`minimax`, `mistral`, `elevenlabs`, `deepinfra`, … and configure the matching
`tts.<provider>` block.

## telemetry — shared metrics

```yaml
telemetry:
  shared_metrics:
    enabled: false                # collect allowlisted aggregate counters
    send: false                   # separate opt-in to actually upload
```

Nothing leaves the machine unless **both** `enabled` and `send` are true. Packages
carry a random profile-scoped ID (no hardware/account/host data); local history is
retained 30 days.

## Model configuration flow

1. **Pick a provider.** Run `iris model` (interactive picker) or set
   `model.provider` in `config.yaml`. `auto` detects from whichever credentials are
   present. First-party OAuth providers sign in with `iris auth add <provider>`
   (e.g. `iris auth add nous`, `iris auth add openai-codex`).
2. **Configure the API key.**
   - Built-in providers: put the key in `$IRIS_HOME/.env`, e.g.
     `OPENROUTER_API_KEY=...`, `ANTHROPIC_API_KEY=...`, `GLM_API_KEY=...`,
     `KIMI_API_KEY=...`, `MINIMAX_API_KEY=...`.
   - Custom endpoint: under `custom_providers` (inline `api_key`, or
     `key_env: VAR_NAME` to read from the environment).
   - Named/enterprise gateway: under `providers.<name>` with `api_key`, `key_env`,
     or `key_cmd` (a command that prints a fresh short-lived bearer).
3. **Set `base_url`** when targeting a non-default endpoint — on `model.base_url`
   for the primary, or per-entry in `providers:` / `custom_providers`.
4. **Override the default model** with `model.default`, the `--model` flag, or the
   in-session `/model` command. Short names can be aliased under `model_aliases`.
5. **Fallback:** list secondary routes under `fallback_providers`; on a transient
   outage the primary is tried first, then the chain. Auxiliary side tasks
   (vision, web extraction, compression, title generation) use the `auxiliary.*`
   blocks and default to auto-detected cheap models.

## Environment variables

Iris loads `$IRIS_HOME/.env` on startup. The variables below are the ones an
operator actually sets; internal plumbing vars (session-scoped, launcher-injected,
TUI sidecar, kanban/update machinery) are not listed.

### Core paths & profiles

| Variable | Purpose | Default | Component |
|---|---|---|---|
| `IRIS_HOME` | Iris data/config directory | `~/.iris` (`%LOCALAPPDATA%\iris` on Windows) | all |
| `IRIS_CONFIG_PATH` / `IRIS_CONFIG` | Override `config.yaml` path | `$IRIS_HOME/config.yaml` | all |
| `IRIS_ENV_PATH` | Override `.env` path | `$IRIS_HOME/.env` | all |
| `IRIS_PROFILE` / `IRIS_PROFILE_NAME` | Activate a named profile | unset (default profile) | all |
| `IRIS_IGNORE_USER_CONFIG` | `1` = run once with built-in defaults, ignore `config.yaml` | unset | all |
| `IRIS_HOME_MODE` | Force `chmod` mode on `$IRIS_HOME` (e.g. `0701`) | unset | all |
| `IRIS_UID` / `IRIS_GID` | Ownership applied to profile subdirs (Docker) | unset | all |

### Model & runtime behavior

| Variable | Purpose | Default | Component |
|---|---|---|---|
| `IRIS_MODEL` | Override the model for one invocation | unset | agent |
| `IRIS_INFERENCE_MODEL` / `IRIS_INFERENCE_PROVIDER` | Pin model/provider | unset | agent |
| `IRIS_API_KEY` | Generic OpenAI-compatible key for `custom` provider | unset | agent |
| `IRIS_BASE_URL` | Generic OpenAI-compatible base URL for `custom` | unset | agent |
| `IRIS_API_TIMEOUT` | Per-request API timeout (seconds) when no config set | `1800` | agent |
| `IRIS_API_CALL_STALE_TIMEOUT` | Non-stream stale-call detector (seconds) | `90` | agent |
| `IRIS_LOCAL_STREAM_STALE_TIMEOUT` | Override stale detector for local endpoints | unset | agent |
| `IRIS_MAX_ITERATIONS` | Cap tool-calling iterations | unset (uses `agent.max_turns`) | agent |
| `IRIS_YOLO_MODE` | `1` = approvals `off` equivalent | unset | agent |
| `IRIS_ACCEPT_HOOKS` | `1` = auto-accept shell hooks (non-TTY runs) | unset | hooks |
| `IRIS_ROOM_LINK_URL` | Public HTTPS base URL for cross-gateway Group Chat | unset | gateway |
| `IRIS_RESTART_AFTER_TURN_TIMEOUT` | In-band wait for in-flight turns before restart (s) | `1800` | gateway |
| `IRIS_RESTART_DRAIN_TIMEOUT` / `IRIS_CRON_DRAIN_TIMEOUT` | Graceful drain on stop/restart (s) | `0` / `30` | gateway |
| `IRIS_TURN_LEASE_TIMEOUT` | Alias-routing wait for a busy session lease (s) | `5` | gateway |
| `IRIS_SESSION_STALL_TIMEOUT` | Session-stall watchdog (s, `0` = off) | `300` | gateway |
| `IRIS_TOOL_PROGRESS` / `IRIS_TOOL_PROGRESS_MODE` | Override `display.tool_progress` | unset | display |
| `IRIS_VERIFY_ON_STOP` | `1`/`0` override for `agent.verify_on_stop` | unset | agent |
| `IRIS_LOCAL_STT_LANGUAGE` | STT language fallback | unset | stt |

### Web UI (WebUI process)

| Variable | Purpose | Default | Component |
|---|---|---|---|
| `IRIS_WEBUI_AGENT_DIR` | Agent source checkout directory | auto-detected | webui |
| `IRIS_WEBUI_PYTHON` | Python executable for the agent venv | auto-detected | webui |
| `IRIS_WEBUI_HOST` | Bind address | `127.0.0.1` | webui |
| `IRIS_WEBUI_PORT` | Listen port | `8787` | webui |
| `IRIS_WEBUI_STATE_DIR` | Sessions/workspaces/state directory | `~/.iris/webui` | webui |
| `IRIS_WEBUI_DEFAULT_WORKSPACE` | Default workspace on first launch | `~/workspace` | webui |
| `IRIS_WEBUI_DEFAULT_MODEL` | Model override for the UI | unset (active provider default) | webui |
| `IRIS_WEBUI_BOT_NAME` | Display name in the UI | `Iris` | webui |
| `IRIS_WEBUI_PASSWORD` | Login password (**required** if bound beyond loopback) | unset | webui |
| `IRIS_WEBUI_PASSKEY` | `1` = enable passkey/WebAuthn login | off | webui |
| `IRIS_WEBUI_SESSION_TTL` | Auth cookie lifetime (seconds) | `2592000` (30 days) | webui |
| `IRIS_WEBUI_SECURE` | Force `Secure` flag on auth cookies | auto-detect | webui |
| `IRIS_WEBUI_ALLOWED_ORIGINS` | Extra allowed CSRF origins (comma-separated, scheme required) | unset | webui |
| `IRIS_WEBUI_TLS_CERT` / `IRIS_WEBUI_TLS_KEY` | Serve HTTPS directly | unset (plain HTTP) | webui |
| `IRIS_WEBUI_TRUSTED_AUTH_HEADER` | Reverse-proxy SSO identity header | unset (disabled) | webui |
| `IRIS_WEBUI_TRUSTED_PROXY_CIDRS` | Allowlisted proxy CIDRs for trusted-header auth | loopback only | webui |
| `IRIS_WEBUI_ATTACHMENT_DIR` | Chat attachment storage | `<state dir>/attachments` | webui |
| `IRIS_WEBUI_PLUGINS_DIR` | WebUI plugin directory | `~/.iris/plugins` | webui |
| `IRIS_WEBUI_GATEWAY_API_KEY` | Key for polling the gateway health endpoint | unset | webui |
| `IRIS_PLUGINS_DEBUG` | `1` to print plugin-load debug logs | unset | plugins |

### Dashboard / gateway OAuth

| Variable | Purpose | Default | Component |
|---|---|---|---|
| `IRIS_DASHBOARD_OAUTH_CLIENT_ID` | Nous Portal OAuth client id | unset (portal provisions) | dashboard |
| `IRIS_DASHBOARD_PORTAL_URL` | Portal base URL | `https://portal.nousresearch.com` | dashboard |
| `IRIS_DASHBOARD_PUBLIC_URL` | Force absolute public URL (behind reverse proxy) | unset | dashboard |
| `IRIS_DASHBOARD_OIDC_ISSUER` / `..._CLIENT_ID` / `..._SCOPES` / `..._CLIENT_SECRET` | Self-hosted OIDC (Authentik/Keycloak/…) | unset | dashboard |

> Telemetry is controlled **only** by the `telemetry.shared_metrics` config block —
> there is no `IRIS_TELEMETRY` env var.

## Applying changes

After editing `config.yaml`, **restart the Web UI / gateway** for it to take effect:

```bash
# stop the old process, then
cd webui && python3 server.py
```

> If you see `agent_runtime_stale`, it means agent source or config changed while the
> server was running — restart the Web UI to recover. This is a safety guard, not a bug.
