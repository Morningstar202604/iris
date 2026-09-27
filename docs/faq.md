# FAQ — Frequently Asked Questions

**English** · [简体中文](faq.zh-CN.md)

## 1. Tasks keep failing with `HTTP 429` (rate limited)

**Cause**: the model service limits free users by rate / total usage.

**Fix**:
- Free quotas are **sliding-window** — wait a bit (minutes) and it resets by itself;
  **do not retry in a tight loop**, that only extends the limit.
- Iris retries 429 with exponential backoff (3 attempts), then reports the limit.
- For heavy use, upgrade to a paid plan (Token Plan etc.) on the provider side.

## 2. `agent_runtime_stale` after startup

**Cause**: agent source or `config.yaml` changed while the Web UI was running, so the
UI can't confirm a safe update.

**Fix**: restart the Web UI (`Ctrl+C`, then `python3 server.py` again). It is a safety
guard, not a failure.

## 3. Skills panel won't open / `No module named 'agent'`

**Cause**: the Web UI cannot find the agent source directory.

**Fix**: point it explicitly:

```bash
HERMES_WEBUI_AGENT_DIR=/path/to/iris/agent python3 server.py
```

## 4. Every request is slow (seconds of latency)

**Cause**: Iris probes the model's context length; on custom endpoints a slow probe
hurts the experience.

**Fix**:
- Set `context_length: 128000` under `model` in `config.yaml` (use your model's real
  window) to skip probing.
- Switch to a lower-latency endpoint.

## 5. A task stops mid-way with no output

**Likely cause**: script tools such as `execute_code` are waiting for approval
(unattended runs).

**Fix**: set `approvals.mode: smart` (see [configuration.md](configuration.md#approvals--approvals)),
so safe commands run automatically.

## 6. Image tool is missing (not in the tool list)

**Cause**: no `image_gen` backend configured.

**Fix**: enable the `image_gen/openai` plugin and point it at an OpenAI-compatible
endpoint (see [quickstart.md](quickstart.md#image-generation-optional)).

## 7. Conversation history suddenly got shorter

**Fix**: Iris compacts history automatically near the context limit and continues the
task — normal memory management. Full session files remain on disk (`~/.hermes/sessions/`).

## 8. How do I uninstall completely?

```bash
# remove state and config
rm -rf ~/.hermes
# remove the project
rm -rf iris
```

## 9. Where is my data? Is it uploaded?

- Sessions, memory, knowledge base and tasks live **on your machine**: `~/.hermes/`.
- Iris itself has **no account, no telemetry**. Only the model provider you configured
  receives conversation requests (data flow is decided by your provider).
- Knowledge-base search happens locally — your documents are not uploaded.

## 10. Can I use a non-OpenAI-compatible model?

Iris is **protocol-first**: any endpoint speaking the OpenAI Chat Completions protocol
(the vast majority of hosted services) can be wired in via `custom_providers`.
