# Iris WebUI — Docker setup guide

This is the comprehensive Docker reference. For a 5-minute quickstart, see the [README Docker section](../README.md#docker).

## TL;DR — pick one

| Setup | When to use | File |
|---|---|---|
| **Single-container** (recommended) | You just want chat working. WebUI runs the agent in-process. | `docker-compose.yml` |
| **Two-container** | You want isolation between gateway (CLI/Telegram/cron) and chat UI. | `docker-compose.two-container.yml` |
| **Three-container** | Two-container PLUS the dashboard for monitoring. | `docker-compose.three-container.yml` |
| **All-in-one image** (community fork — third-party, not maintained by us) | Podman 3.4 / multi-arch / supervisord-style preference. | [sunnysktsang/iris-suite](https://github.com/sunnysktsang/iris-suite) — see [#1399](https://github.com/nesquena/hermes-webui/issues/1399) for the original discussion |

### Available Docker tags

> **[CHANNEL-PENDING]** The old `ghcr.io/nesquena/iris-webui` / `nousresearch/iris-agent`
> images are upstream dead links. This project's images are not yet published to a
> registry. **Recommended target** once the registry is stood up:
> `ghcr.io/x33834/iris-webui` (WebUI) and `ghcr.io/x33834/iris-agent` (agent).
> Confirm the published registry + tag before `docker pull`; see MIRROR.md for the
> dual-track release hosts. The tag *scheme* below still applies to whichever
> registry hosts the image.

The WebUI Docker image will be published to `ghcr.io/x33834/iris-webui` (recommended; pending registry confirmation) with these tags:

| Tag | Channel | Description |
|---|---|---|
| `:latest` | stable | The most recent stable release (from `v*` tags). Suitable for production. |
| `:experimental` | experimental | The most recent experimental release (from `exp-v*` tags). For early testing; may include breaking changes or unfinished features. Do not run in production. |
| `:X.Y` / `:X.Y.Z` | stable | Pinned stable releases (e.g., `:1.5`, `:1.5.0`). |
| `:X.Y` / `:X.Y.Z` | experimental | Pinned experimental releases — same version numbers but pushed from `exp-v*` tags. The `:experimental` floating tag always points at the latest of these. |

To track experimental builds in Docker Compose, use the `:experimental` tag:

```yaml
services:
  iris-webui:
    image: ghcr.io/x33834/iris-webui:experimental  # [CHANNEL-PENDING] confirm registry
```

> **Note:** updating between `:experimental` builds requires `docker compose pull` followed by `docker compose up -d` — the floating tag is updated only when a new `exp-v*` release is pushed. Experimental builds are not pushed on every commit to the default branch.

> **Note (v0.14+):** If you use `docker-compose.three-container.yml`, both
> `iris-agent` and `iris-dashboard` initialise from the same image and write
> to the same `iris-home` volume simultaneously. This can cause overlapping lock
> files and stale `gateway_state.json` entries. The unified pattern described in
> [Three-service unified setup (v0.14+)](#three-service-unified-setup-v014) below
> avoids this by running a single `iris-agent` process that serves both the
> gateway and the dashboard.

If something stops working, **start with the single-container setup** — it's the simplest path and fixes most permission/UID/path-mismatch issues by construction.

## Production image security model

The production Docker image is hardened for the normal single-tenant container threat model:
Iris WebUI assumes one operator controls the container, mounted Iris home, and workspace.
The image does **not** install `sudo`, does not add runtime users to a sudo group, and does not
grant `NOPASSWD` escalation. If an agent/tool process gains a shell as `iriswebui`, it should
not be able to become root with a passwordless sudo command.

The entrypoint still starts as `root` for a narrow init phase because Docker bind mounts often need
UID/GID alignment and ownership preparation before the app can read `~/.iris`, `/workspace`,
`/app`, and `/uv_cache`. After that setup, `docker_init.bash` re-execs itself as the unprivileged
`iriswebui` user and starts the server there. Init scratch files under `/tmp/iriswebui_init`
are owner-only (`0700` directory, `0600` files), not world-writable.

For multi-tenant or hostile-container environments, rebuild with your own runtime user, mount policy,
and supervisor assumptions. Development images that need package-manager convenience should add
those tools in a dev-only Dockerfile instead of reintroducing passwordless sudo to production.

## 5-minute quickstart (single container)

```bash
# GitHub primary; China users can use the GitCode mirror:
#   git clone https://gitcode.com/badhope/iris.git
git clone https://github.com/X33834/iris.git
cd iris-webui
cp .env.docker.example .env
# Edit .env if needed (most users can skip this on Linux)
docker compose up -d
open http://localhost:8787
```

That's it for a real personal Docker install. Your existing `~/.iris`
directory is mounted, your `~/workspace` is browsable, and the WebUI
auto-detects your UID/GID from the mounted volume.

The single-container setup runs the WebUI only. It can create cron jobs and run
them manually from the Tasks panel. In Docker, scheduled jobs require the Iris gateway daemon
to tick while you are away. If System Settings shows `Gateway not configured`,
use `docker-compose.two-container.yml`,
`docker-compose.three-container.yml`, or run `iris gateway` separately before
relying on offline scheduled runs. See [Scheduled jobs and the gateway daemon](#scheduled-jobs-and-the-gateway-daemon) below for the full background and verification steps.

For troubleshooting, reinstall, or onboarding reproduction trials, do not mount
your real `~/.iris` unless you intentionally want to test real state. Use an
isolated Iris home and follow
[`docs/onboarding-agent-checklist.md`](onboarding-agent-checklist.md) instead.

> **Linux note**: run Compose as the user who owns the Iris home. The command
> `sudo docker compose up -d` can make Compose expand `${HOME}` as `/root`, so
> the default `${HOME}/.iris` bind mount becomes `/root/.iris` instead of
> your user's real Iris directory. Prefer adding your user to the `docker group`
> and running `docker compose up -d`; if you must preserve the caller environment
> for a one-off root run, use `sudo -E docker compose up -d` and verify the
> rendered mount with `docker compose config` first.

## Optional GPU runtime image

The default Iris WebUI Docker image stays CPU-only. GPU user-space packages
are installed only when you build a custom image with the opt-in build arg:

```bash
docker build --build-arg INSTALL_GPU_LIBS=1 -t iris-webui:gpu .
```

That build path installs VA-API basics (`libva2`, `vainfo`), AMD Mesa VA-API
drivers (`mesa-va-drivers`), and the Intel non-free media driver when that
package is available from the configured Debian repositories. NVIDIA host
runtime tooling is not installed into the app image; use the NVIDIA Container
Toolkit on the host and pass GPUs through at runtime.

GPU passthrough still depends on host drivers, Docker runtime support, and
device mappings. The commands below are configuration guidance for a suitable
Linux Docker host; they are not a claim that native GPU passthrough was verified
in this workspace.

### Intel and AMD VA-API

Expose the host render devices and add the runtime user to the common video and
render groups:

```bash
docker run --rm \
  --device /dev/dri:/dev/dri \
  --group-add video \
  --group-add render \
  iris-webui:gpu vainfo
```

For Compose, add the same mapping to a custom service definition:

```yaml
services:
  iris-webui:
    image: iris-webui:gpu
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - video
      - render
```

`vainfo` should list the VA-API driver and supported profiles when the host
driver stack and container permissions are correct. The container entrypoint
preserves Docker-provided supplemental groups before it drops privileges to the
`iriswebui` runtime user, so the WebUI process keeps access to `/dev/dri`.

### NVIDIA

Install and configure the NVIDIA Container Toolkit on the host first, then use
Docker's GPU runtime flag:

```bash
docker run --rm --gpus all iris-webui:gpu nvidia-smi
```

For Compose, use a custom service with GPU access enabled:

```yaml
services:
  iris-webui:
    image: iris-webui:gpu
    gpus: all
```

If `nvidia-smi` is unavailable or reports no devices, fix the host NVIDIA driver
and container toolkit setup before debugging Iris WebUI. The container image
only supplies the WebUI plus optional user-space media libraries; it cannot
provide host kernel drivers or the NVIDIA runtime.

## Scheduled jobs and the gateway daemon

**Symptom**: Cron jobs created in the Tasks panel never fire. System Settings or Tasks shows:

- Orange "Gateway not configured", or
- Red "Gateway metadata stale" when runtime metadata is stale, or
- Red "Gateway endpoint not reachable" when WebUI has a gateway URL configured but cannot reach its health endpoint.

**Cause**: Scheduled cron ticks are not driven by the WebUI itself. The gateway daemon ticks the scheduler every 60 seconds; without one running, scheduled jobs sit idle. "Run now" / "Trigger" buttons still work because the WebUI handles those in-process.

The cron list itself is still read from the shared `IRIS_HOME` volume, not
from the gateway HTTP API. If the Tasks panel shows a gateway warning while the
job list loads, the warning is about scheduled ticking / gateway health, not
about the list endpoint.

In older gateway builds, or when the daemon runs in a separate container, `gateway_state.json` can become stale and WebUI may lose confidence even if the daemon is up. This is especially visible if the WebUI container has no gateway URL and can only inspect local state files from its own container.

**Fix**: Run a gateway container alongside the WebUI. The two-container compose file is the recommended path:

```bash
cp .env.docker.example .env
docker compose -f docker-compose.two-container.yml up -d
```

The compose files forward `API_SERVER_KEY` from `.env` into the `iris-agent`
container. The agent only starts the gateway API listener (port 8642) when
`API_SERVER_KEY` is a usable value (>=16 chars) — `API_SERVER_ENABLED` alone
does nothing. Without a key, the gateway daemon still runs but port 8642 stays
unbound and the WebUI keeps showing **"Gateway endpoint not reachable"**. To
enable scheduled ticking and the green gateway pill, set a long random string
in `.env`:

```bash
echo "API_SERVER_KEY=$(openssl rand -hex 24)" >> .env
docker compose -f docker-compose.two-container.yml up -d --force-recreate
```

The compose file forwards the same value to the WebUI as
`IRIS_WEBUI_GATEWAY_API_KEY`, so the health probe authenticates automatically.

The three-container layout adds the dashboard but is otherwise the same shape. If you must stay single-container, you can run `iris gateway` inside the container as a long-lived background process, but the compose split is sturdier.

If you maintain a custom compose file, make sure the **WebUI service** points at
the gateway service over the compose network:

```yaml
services:
  iris-webui:
    environment:
      - IRIS_API_URL=http://iris-agent:8642
      # IRIS_WEBUI_GATEWAY_BASE_URL=http://iris-agent:8642 also works.
```

If WebUI browser chat is routed through that gateway and you expect approval prompts for guarded tools, set the gateway chat backend and opt into the runs API path in the **WebUI service**:

```yaml
services:
  iris-webui:
    environment:
      - IRIS_WEBUI_CHAT_BACKEND=gateway
      - IRIS_WEBUI_GATEWAY_BASE_URL=http://iris-agent:8642
      - IRIS_WEBUI_GATEWAY_USE_RUNS_API=true
      # IRIS_WEBUI_GATEWAY_API_KEY=... when the gateway requires API auth.
```

`IRIS_WEBUI_GATEWAY_USE_RUNS_API=true` is required for gateway approval cards because approval-capable gateway runs emit approval requests on the runs API transport. Leaving it unset keeps browser chat on the legacy chat-completions path.

Do not copy only `API_SERVER_ENABLED=true` / `API_SERVER_HOST=0.0.0.0` into the
agent service as a standalone fix. If you intentionally enable the agent API
server, the agent also requires a real `API_SERVER_KEY` (at least 8 characters),
and the WebUI still needs `IRIS_API_URL` or `IRIS_WEBUI_GATEWAY_BASE_URL` to
reach that service from its container.

**Verify**: Once the gateway is up, the System Settings pill should turn green and the Tasks banner disappear. From the host:

```bash
export GATEWAY_BASE_URL="${IRIS_API_URL:-${IRIS_WEBUI_GATEWAY_BASE_URL:-http://iris-agent:8642}}"
docker compose -f docker-compose.two-container.yml exec iris-agent iris gateway status
curl -sS "${GATEWAY_BASE_URL%/}/health/detailed" | jq '.gateway_state, .state'
```

If the service name differs in your compose file, `docker compose -f docker-compose.two-container.yml ps` lists the running services.
For container-to-container diagnostics, set one of `IRIS_API_URL` or `IRIS_WEBUI_GATEWAY_BASE_URL` in the WebUI environment, then restart WebUI.

Refs #2785, #4483.

## Three-service unified setup (v0.14+)

Since v0.14, `iris-agent` can serve the gateway API and the built-in dashboard
from the same process by setting `IRIS_DASHBOARD_HOST` and
`IRIS_DASHBOARD_PORT`. Running agent and dashboard in one container means a
single writer to `iris-home`, eliminating the concurrent-init write conflicts
that occur when `iris-agent` and `iris-dashboard` both start from the same
image against the same volume.

The three-service pattern uses two containers:

| Service | Image | Ports |
|---|---|---|
| `iris-agent` | `ghcr.io/x33834/iris-agent:latest` *(recommended, [CHANNEL-PENDING])* | 8642 (gateway), 9119 (dashboard) |
| `iris-webui` | `ghcr.io/x33834/iris-webui:latest` *(recommended, [CHANNEL-PENDING])* | 8787 (chat UI) |

> Images below are the recommended targets; the old `nousresearch/iris-agent` and
> `ghcr.io/nesquena/iris-webui` tags are upstream dead links. Confirm the registry
> has published them before pulling.

Example compose snippet (save as `docker-compose.three-service.yml` or inline into your own file):

```yaml
services:
  iris-agent:
    image: ghcr.io/x33834/iris-agent:latest  # [CHANNEL-PENDING] confirm registry
    container_name: iris-agent
    command: gateway run
    ports:
      - "127.0.0.1:8642:8642"
      - "127.0.0.1:9119:9119"
    volumes:
      - iris-home:/home/iris/.iris
      - iris-agent-src:/opt/iris
    environment:
      # IRIS_HOME is honored first; IRIS_HOME remains as the fallback name.
      - IRIS_HOME=/home/iris/.iris
      - IRIS_UID=${UID:-1000}
      - IRIS_GID=${GID:-1000}
      - IRIS_DASHBOARD_HOST=0.0.0.0
      - IRIS_DASHBOARD_PORT=9119
    restart: unless-stopped
    networks:
      - iris-net

  iris-webui:
    image: ghcr.io/x33834/iris-webui:latest  # [CHANNEL-PENDING] confirm registry
    container_name: iris-webui
    depends_on:
      - iris-agent
    ports:
      - "127.0.0.1:8787:8787"
    volumes:
      - iris-home:/home/iriswebui/.iris
      - iris-agent-src:/home/iriswebui/.iris/iris-agent:ro
      - ${IRIS_WORKSPACE:-${HOME}/workspace}:/workspace
    environment:
      - IRIS_WEBUI_HOST=0.0.0.0
      - IRIS_WEBUI_PORT=8787
      - IRIS_WEBUI_STATE_DIR=/home/iriswebui/.iris/webui
      - WANTED_UID=${UID:-1000}
      - WANTED_GID=${GID:-1000}
    restart: unless-stopped
    networks:
      - iris-net

networks:
  iris-net:
    driver: bridge

volumes:
  iris-home:
  iris-agent-src:
```

Open http://localhost:8787 for chat and http://localhost:9119 for the dashboard.
Check `iris gateway run --help` for the exact flag names for your agent release —
the env-var equivalents shown above (`IRIS_DASHBOARD_HOST`, `IRIS_DASHBOARD_PORT`)
are available in recent releases alongside the CLI flags.

If you need the separate dashboard container (e.g. resource limits per service),
`docker-compose.three-container.yml` still works. Add a `depends_on` from
`iris-dashboard` to `iris-agent` with a `condition: service_healthy` healthcheck
so the dashboard waits for the gateway to finish initialising agent-home before it
starts its own init pass.

## What goes wrong (and how to fix it)

### Compatibility policy and version pinning

WebUI shows the version it is currently running, but that display does not in itself guarantee tested compatibility with your agent release.

Until the compatibility boundary work in [#1925](https://github.com/nesquena/hermes-webui/issues/1925) and [#2491](https://github.com/nesquena/hermes-webui/issues/2491) land, the WebUI and Iris Agent deployment should be treated as a release pair: the WebUI release is tested against its matching agent release and should be upgraded/pinned together.

If you use `latest`, use it consistently on both sides and avoid mixing a fixed tag with `latest`:
- fixed WebUI tag + `iris-agent:latest`
- `iris-webui:latest` + fixed `iris-agent` tag

In multi-container setups, if you must run a pinned pair, prefer the matching tag in `docker-compose.two-container.yml`/`docker-compose.three-container.yml` and perform the agent-volume refresh workflow in [Upgrading the agent container](#upgrading-the-agent-container) whenever you upgrade the agent image.

If you see behavior issues after a mixed-version upgrade, capture both WebUI and iris-agent versions and the compose layout in the issue.

### 1. "Permission denied" at startup

**Symptom**: Container starts but immediately crashes, logs show:
```
PermissionError: [Errno 13] Permission denied: '/home/iriswebui/.iris/...'
```

**Cause**: The container's user (UID 1000 by default) can't read your bind-mounted directory because your host files are owned by a different UID.

**Fix**: Set `UID` and `GID` in `.env` to match your host:
```bash
echo "UID=$(id -u)" >> .env
echo "GID=$(id -g)" >> .env
docker compose down && docker compose up -d
```

On macOS, host UIDs start at 501. On Linux, the first interactive user is usually UID 1000.

> **macOS Docker Desktop**: if UID mapping still misbehaves after the env fix, try toggling **Settings → General → File sharing implementation** between VirtioFS and gRPC-FUSE. Different implementations preserve UIDs across the host/container boundary differently.

### 2. ".env file mode 0640 → permission denied" (#1389)

**Symptom**: You set `IRIS_HOME_MODE=0640` (or some other group-readable mode) on your host `.env` file, container starts, then errors out:
```
[security] fixed permissions on .env (0o640 -> 0600)
failed to load .env: open .env: permission denied
```

**Cause**: WebUI's `fix_credential_permissions()` startup hook enforces 0600 by default. This is the right thing for a clean install but conflicts with operator-set modes.

**Fix**: Set one of these env vars in your `.env`:
- `IRIS_SKIP_CHMOD=1` — bypass the fixer entirely
- `IRIS_HOME_MODE=0640` — allow group bits, only strip world-readable

Both are documented in `api/startup.py::fix_credential_permissions()`.

> ⚠️ **Multi-container warning**: `IRIS_HOME_MODE` has DIFFERENT semantics in the agent image vs. the WebUI:
> - **WebUI**: credential FILE mode threshold (`0640` allows group bits on `.env`)
> - **Agent**: `IRIS_HOME` *directory* mode (default `0700`)
>
> `0640` on a directory has no owner-execute bit, so the agent can't traverse its own home → bricked. For multi-container setups, use `IRIS_HOME_MODE=0750` (group-traversable) or `0701` (x-only). The compose files have per-service comments that match each side's semantics.

### 3. "Workspace appears empty even though my files are there"

**Symptom**: WebUI loads but `/workspace` shows no files.

**Cause**: Same as #1 — UID mismatch on the bind mount.

**Fix**: Same as #1 — match host UID/GID via `.env`.

### 4. "Two-container setup: WebUI can't find agent source" (#858)

**Symptom**: WebUI logs at startup:
```
!! WARNING: iris-agent source not found.
!!   Looked in: /home/iriswebui/.iris/iris-agent
!!              /opt/iris
```

**Cause**: The agent's source (`/opt/iris` inside the agent container) needs to be exposed to the WebUI container via a shared volume. The two-container compose file does this via `iris-agent-src` named volume, but if you're using bind mounts incorrectly the path won't resolve.

**Fix**: Use the named volumes that ship with `docker-compose.two-container.yml` — don't replace them with bind mounts unless you know what you're doing. The agent container writes its source to `/opt/iris`, and the WebUI mounts that volume at `/home/iriswebui/.iris/iris-agent`.

If you must use a bind mount: pick a host path, then mount it to `/opt/iris` in the agent container AND `/home/iriswebui/.iris/iris-agent` in the WebUI container.

### 5. "Tools (git, node, etc.) missing in two-container setup" (#681)

**Symptom**: You ask the agent to run `git status` in chat and it errors with `command not found`.

**Cause**: This is **architectural, not a bug**. In the two-container setup, agent processes started by the WebUI run **inside the WebUI container**, not the agent container. The WebUI image doesn't include git/node by design (it's a UI image, not a tool host).

**Workarounds**:
- **Single-container setup** (`docker-compose.yml`) — everything in one container, no boundary
- **Custom WebUI image** — extend the `Dockerfile` to install the tools you need
- **Combined image** ([sunnysktsang/iris-suite](https://github.com/sunnysktsang/iris-suite)) — community fork that ships agent+webui+dashboard in one container

### 6. "config.yaml not loaded"

**Symptom**: You have a `config.yaml` in your host `~/.iris/`, but the WebUI shows "no model configured" or doesn't pick up your custom providers.

**Cause**: Either the file isn't readable (UID/GID issue, see #1) or it's not in the expected path inside the container.

**Fix**:
- Verify: `docker exec iris-webui ls -la /home/iriswebui/.iris/config.yaml`
- If it doesn't exist: your host bind mount is pointing at the wrong directory.
- If it exists but is unreadable: see #1 for the UID/GID fix.

### 7. "On Podman: can't share .iris between containers"

**Symptom**: Two-container setup works on Docker but fails on Podman with permission errors no matter what UID/GID you set.

**Cause**: Podman 3.4 (Ubuntu 22.04 default) has limited support for `userns_mode: keep-id` across multiple containers — files written by one container appear with a different UID in the other.

**Fix**: Either upgrade to Podman 4+ (which fixes this), or use the [single-container setup](#5-minute-quickstart-single-container), or use the [community all-in-one image](https://github.com/sunnysktsang/iris-suite).

### 8. "API base URL set to localhost fails from Docker" (#3012)

**Symptom**: A provider, local model server, webhook, or custom API works on the host at `http://localhost:<port>`, but fails when the same URL is configured in Iris WebUI running in Docker.

**Cause**: Inside a container, `localhost` means *that container*, not your laptop/host. The WebUI process cannot reach host services through `127.0.0.1` unless the service is running inside the same container.

**Fix**: Point Docker-hosted WebUI at the host gateway name instead:

- Docker Desktop on macOS/Windows: `http://host.docker.internal:<port>`
- Podman: `http://host.containers.internal:<port>`
- Linux Docker Engine: either publish the host service on the Docker bridge address, or add a host-gateway alias to your compose service:

```yaml
services:
  iris-webui:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Then configure the URL as `http://host.docker.internal:<port>`. Also ensure the host service binds to an address reachable from containers (not only a loopback interface the Docker bridge cannot reach) and that your host firewall allows the connection.

### 9. "Failed to verify state directory" / restart loop on a bind-mounted state dir (#7027)

**Symptom**: Single-container deploy with the state directory bind-mounted from a
host directory, no `WANTED_UID` set. The container exits 1 and restart-loops:

```
-- Auto-detected workspace UID: 1024 (from /workspace)
touch: cannot touch '/app/data/.testfile': Permission denied
!! ERROR: Failed to verify state directory at /app/data
```

**Cause**: UID auto-detection used to read `/workspace` before the configured
state directory. In a stock image `/workspace` exists and is owned by the
image's own build-time `1024:1024`, so detection returned a value that carries
no information about the host — and because `1024` is also the fallback default,
the log read as if detection had found nothing.

**Fix**: Fixed in the init script — the configured `IRIS_WEBUI_STATE_DIR` is
now probed first. The full order is:

1. `$IRIS_WEBUI_STATE_DIR` (default `/app/data`) — a bind mount by definition
   in a single-container deploy, so its owner is the host identity to match
2. `/home/iriswebui/.iris`, `$IRIS_HOME`, `/opt/data` — the iris-home
   shared volume in two-container setups (#668)
3. `/workspace` — used only when nothing above resolves
4. `1024` — fallback default

Root-owned candidates (UID 0, e.g. a freshly created named volume) are skipped
at every step. An explicitly supplied `WANTED_UID`/`WANTED_GID` always wins and
is never overwritten by detection — including the value `1024`, which earlier
versions treated as "unset".

If you are on an older image, the workaround is to set the IDs explicitly:

```bash
docker run -e WANTED_UID=$(id -u) -e WANTED_GID=$(id -g) ...
```

## Multi-container architecture

The two- and three-container setups use **named Docker volumes** (not bind mounts) by default for a reason: named volumes solve the UID/GID problem by construction. Docker creates the volume's root directory with the correct ownership, all containers reading/writing to it see the same files, no host-side permission setup required.

```
                 ┌─────────────────────────────────┐
                 │      iris-home (volume)       │
                 │  (config, sessions, state, ...)  │
                 └─────────────────────────────────┘
                          ↑              ↑
                          │ rw           │ rw
                          │              │
      ┌──────────────┐    │              │    ┌──────────────┐
      │ iris-agent │────┘              └────│ iris-webui │
      │  (port 8642) │                        │  (port 8787) │
      └──────────────┘                        └──────────────┘
              │                                       ↑
              │ rw                                    │ ro
              ↓                                       │
      ┌─────────────────────────┐                     │
      │ iris-agent-src (vol)  │─────────────────────┘
      │ (agent's Python source) │
      └─────────────────────────┘
```

The WebUI container doesn't ship with the agent's Python deps — at startup it runs `uv pip install /home/iriswebui/.iris/iris-agent` to install them from the shared volume. The WebUI mount is read-only; the agent container is the only writer.

## Upgrading the agent container

The `iris-agent-src` named volume is initialised from the agent image's `/opt/iris` on first `up`. Docker reuses the volume verbatim on every subsequent `up` — **even after `docker pull` of a newer agent image**. The cached volume content masks the new image's source tree, so a fresh `docker pull` of `ghcr.io/x33834/iris-agent:latest` (recommended; [CHANNEL-PENDING]) does not by itself give you the new agent code, dependencies, or entrypoint.

This is the root cause of [#1416](https://github.com/nesquena/hermes-webui/issues/1416): the symptom looked like a missing entrypoint, but the entrypoint was actually present in the new image and hidden behind the stale named volume.

To upgrade the agent image cleanly, drop the source volume before recreating:

```bash
# Two-container setup
docker compose -f docker-compose.two-container.yml down
docker volume rm <project>_iris-agent-src
docker compose -f docker-compose.two-container.yml pull
docker compose -f docker-compose.two-container.yml up -d

# Three-container setup
docker compose -f docker-compose.three-container.yml down
docker volume rm <project>_iris-agent-src
docker compose -f docker-compose.three-container.yml pull
docker compose -f docker-compose.three-container.yml up -d
```

Replace `<project>` with your Compose project name (the parent directory by default; check with `docker volume ls`). The `iris-home` volume (config, sessions, state) is left untouched — only `iris-agent-src` (the agent's installed Python source) is recreated.

> The single-container setup (`docker-compose.yml`) does not use `iris-agent-src` and is not affected by this upgrade pattern — pulling a newer WebUI image and `docker compose up -d --force-recreate` is sufficient.

## What the multi-container setup isolates (and what it doesn't)

The two- and three-container setups give you **process, network, and resource isolation** between the gateway and the chat UI:

- Each service has its own PID namespace and lifecycle — the agent process can crash without taking down the chat UI and vice versa.
- The gateway API (port 8642) is bound by the agent service only; the WebUI cannot bind it. Other containers reach the gateway via the `iris-net` Docker network.
- Resource limits (`deploy.resources.limits` in `docker-compose.three-container.yml`) apply per service, so you can cap the agent independently of the dashboard.
- Restart policies, log streams, and container health checks are scoped per service.

What multi-container does **not** isolate:

- **Filesystem boundary.** Both services share `iris-home` (config, sessions, state), and the WebUI mounts the agent's installed source from `iris-agent-src`. The WebUI mount is read-only (since v0.51.84), but the agent service still has write access, and both services share the home volume.
- **UID/GID boundary.** Both services default to `${UID:-1000}` so files written by one are readable by the other. If you align them to different UIDs you'll get permission errors on the shared volume.
- **Trust boundary on the agent source.** The WebUI installs Python dependencies from the shared `iris-agent-src` volume at startup. The read-only mount means a compromised WebUI cannot rewrite the agent source, but it does run code from that volume.

If you need **filesystem isolation** between the chat UI and the agent (e.g. you don't trust the WebUI to read agent state), the multi-container setup is not enough — run the agent on a separate host and connect the WebUI to it via the gateway HTTP API. If you don't need any boundary, the single-container setup is simpler.

The direct source mount is a compatibility bridge, not the long-term API contract. The current source/API boundary inventory and decoupling task list live in [`docs/rfcs/agent-source-boundary.md`](rfcs/agent-source-boundary.md) for [#2453](https://github.com/nesquena/hermes-webui/issues/2453). If you customize the compose files with bind mounts, keep the WebUI-side agent source mount read-only unless you are intentionally doing local development; `docker_init.bash` warns at startup when that path is writable.

## Bind-mount migration (advanced)

If you really need to bind-mount an existing host `~/.iris` (e.g. you're keeping config in dotfiles, sharing with a non-Docker `iris` install, etc.):

```yaml
volumes:
  iris-home:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/youruser/.iris
  iris-agent-src:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/iris-agent-source
```

**Critical requirements**:

1. The host directory MUST be readable by your container UID. Run `id -u` on the host and ensure `~/.iris` is owned by that UID (or readable via group bits).
2. ALL containers sharing the volume must run as the SAME UID/GID. Set `UID=$(id -u)` and `GID=$(id -g)` in `.env`.
3. If you run Compose with sudo, do not rely on `${HOME}` defaults: `sudo` often changes `$HOME` to `/root`, so `${IRIS_HOME:-${HOME}/.iris}` becomes `/root/.iris`. Prefer running Docker as your user; otherwise pass absolute paths with `sudo -E`, for example `IRIS_HOME=/home/youruser/.iris IRIS_WORKSPACE=/home/youruser/workspace sudo -E docker compose up -d`, and confirm the rendered bind mount with `docker compose config`.
4. If your host `.env` is mode 0640, set `IRIS_SKIP_CHMOD=1` or `IRIS_HOME_MODE=0640` so the startup hook doesn't try to enforce 0600.

## Reference

- [`docker-compose.yml`](../docker-compose.yml) — single container (recommended)
- [`docker-compose.two-container.yml`](../docker-compose.two-container.yml) — agent + webui
- [`docker-compose.three-container.yml`](../docker-compose.three-container.yml) — agent + dashboard + webui
- [`.env.docker.example`](../.env.docker.example) — environment variable template
- [`Dockerfile`](../Dockerfile) — single-container build
- [`docker_init.bash`](../docker_init.bash) — container entrypoint script

## Related issues

- #1416 — agent-image upgrade requires removing `iris-agent-src` named volume (see [Upgrading the agent container](#upgrading-the-agent-container))
- #1389 — `IRIS_HOME_MODE` override (fixed in v0.50.254 — agent honors `IRIS_SKIP_CHMOD` and `IRIS_HOME_MODE`)
- #1399 — UID alignment in compose files (fixed in v0.50.260 via PR #1428 + this guide)
- #3012 — host `localhost` API URLs fail from Docker containers (use `host.docker.internal` / `host.containers.internal`)
- #3006 — `sudo docker compose` can mount `/root/.iris` instead of the user's Iris home
- #3243 — optional GPU runtime image/docs for containerized acceleration workloads
- #858 — two-container `/opt/iris` path confusion
- #681 — tools running in WebUI container, not agent container (architectural)
- #668 — auto-detect UID/GID from mounted volume
- #569 — UID/GID detection priority order
- #7027 — state dir probed before `/workspace` in UID/GID detection (see [#9 above](#9-failed-to-verify-state-directory--restart-loop-on-a-bind-mounted-state-dir-7027))

If you hit a new failure mode not covered here, please [open an issue](https://github.com/X33834/iris/issues/new) with:

1. Which compose file you used
2. The error from `docker logs iris-webui`
3. `docker exec iris-webui id` output
4. `docker exec iris-webui ls -la /home/iriswebui/.iris` output
