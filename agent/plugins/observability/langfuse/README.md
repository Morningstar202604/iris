# Langfuse Observability Plugin

This plugin ships bundled with Iris but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
iris tools  # → Langfuse Observability

# Manual
pip install langfuse
iris plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.iris/.env` (or via `iris tools`):

```bash
IRIS_LANGFUSE_PUBLIC_KEY=pk-lf-...
IRIS_LANGFUSE_SECRET_KEY=sk-lf-...
IRIS_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
iris plugins list                 # observability/langfuse should show "enabled"
iris chat -q "hello"              # then check Langfuse for a "Iris turn" trace
```

Generation observations include the Iris system prompt when the provider
uses a separate `system` param (Anthropic Messages API). Open an **LLM call**
child span to inspect `role: system` (truncated via `IRIS_LANGFUSE_MAX_CHARS`).

## Optional tuning

```bash
IRIS_LANGFUSE_ENV=production       # environment tag
IRIS_LANGFUSE_RELEASE=v1.0.0       # release tag
IRIS_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
IRIS_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
IRIS_LANGFUSE_MAX_DEPTH=4          # max payload depth (default: 4)
IRIS_LANGFUSE_CAPTURE=sanitized    # content capture mode (see below)
IRIS_LANGFUSE_DEBUG=true           # verbose plugin logging
```

`IRIS_LANGFUSE_MAX_DEPTH` controls nested payload capture in both `sanitized`
and `full` modes, including tool arguments and JSON tool results. The root is
depth 0; each dictionary value or array element adds one level. Values beyond
the limit become `<max-depth>`, including scalars. For deeper MCP responses,
set it to a higher non-negative integer (for example, `10`) in the Iris
process environment. Unset or blank values default to `4`; invalid or negative
values log a warning and fall back to `4`. `0` keeps only the root level.
Increasing the depth exports more content and may produce larger traces;
secret redaction, string-length limits, and the 50-item collection limit remain
unchanged. `metadata` mode still omits content.

## Capture modes

`IRIS_LANGFUSE_CAPTURE` controls how much *content* (prompts, responses,
tool arguments/results) is exported. Structural metadata — IDs, roles, tool
names, token usage, cost, timing — is always captured in every mode.

| mode | behavior |
|------|----------|
| `metadata` | No content. Each content field is replaced by a shape/size stub (`{"omitted": true, "type": "text", "chars": N}`). |
| `sanitized` | **(default)** Content is exported after secret-pattern redaction (API keys, tokens, JWTs, private keys, `password=`-style assignments) and truncation. Redaction runs *before* truncation. |
| `full` | Raw content, truncated only. Explicit opt-in — traces will contain whatever passed through the conversation, including injected memory and file contents. |

The active mode is recorded on every trace as `metadata.capture_mode`.

Note: `sanitized` is pattern-based defense in depth, not a DLP guarantee.
For personal sessions or shared Langfuse projects, prefer `metadata`.

## Error + shutdown coverage

- Failed model requests (`api_request_error` hook) close their generation
  with `level=ERROR`, status code, retry counters, and a capture-mode-scrubbed
  error message. Non-retryable failures also finish the turn trace.
- Session end/finalize closes any still-open traces for that session and
  flushes queued events, so interrupted or tool-only turns don't dangle.

## Disable

```bash
iris plugins disable observability/langfuse
```
