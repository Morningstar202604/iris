<p align="center">
  <img src="assets/banner.png" alt="Iris Agent" width="100%">
</p>

# Iris Agent ✦
<p align="center">
  <a href="https://gitcode.com/badhope/iris">Iris Agent</a> | <a href="https://gitcode.com/badhope/iris/releases">Iris Releases</a>
</p>
<p align="center">
  <a href="https://gitcode.com/badhope/iris"><img src="https://img.shields.io/badge/Repo-gitcode.com%2Fbadhope%2Firis-4F6EF7?style=for-the-badge" alt="GitCode"></a>
  <a href="https://gitcode.com/badhope/iris/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
</p>

**Iris — the agent core of your personal AI assistant** (a community fork of Hermes, the open-source agent framework originally by Nous Research; upstream 0.21.4 at fork time; fully self-contained, no runtime dependency on the upstream package). It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — [Nous Portal](https://portal.nousresearch.com), OpenRouter, OpenAI, your own endpoint, and [many others](../docs/configuration.md). Switch with `iris model` — no code changes, no lock-in.

<table>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, and CLI — all from a single gateway process. Voice memo transcription, cross-platform conversation continuity.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Compatible with the <a href="https://agentskills.io">agentskills.io</a> open standard.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Built-in cron scheduler with delivery to any platform. Daily reports, nightly backups, weekly audits — all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere, not just your laptop</b></td><td>Seven terminal backends — local, Docker, SSH, Singularity, Modal, Daytona, and Vercel Sandbox. Daytona and Modal offer serverless persistence — your agent's environment hibernates when idle and wakes on demand, costing nearly nothing between sessions. Run it on a $5 VPS or a GPU cluster.</td></tr>
<tr><td><b>Research-ready</b></td><td>Batch trajectory generation, trajectory compression for training the next generation of tool-calling models.</td></tr>
</table>

---

## Quick Install

### Linux, macOS, WSL2, Termux

```bash
# GitHub primary: git clone https://github.com/X33834/iris.git && cd iris/agent
# GitCode mirror (faster in mainland China):
git clone https://gitcode.com/badhope/iris.git && cd iris/agent
./setup-iris.sh
```

### Windows (native, PowerShell)

> **Heads up:** Native Windows runs Iris without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://gitcode.com/badhope/iris/issues).

Run this in PowerShell:

```powershell
git clone https://gitcode.com/badhope/iris.git; cd iris\agent
.\setup-iris.sh
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\iris\git` — no admin required, completely isolated from any system Git install). Iris uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](../docs/quickstart.md). On Termux, Iris installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.
>
> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\iris`; WSL2 installs under `~/.iris` as on Linux.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
iris              # start chatting!
```

### Troubleshooting

#### Windows Defender or antivirus flags `uv.exe` as malware

If your antivirus (Bitdefender, Windows Defender, etc.) quarantines `uv.exe` from the Iris `bin` folder (`%LOCALAPPDATA%\iris\bin\uv.exe`), this is a **false positive**. The file is Astral's `uv` — the Rust Python package manager Iris bundles to manage its Python environment. ML-based antivirus engines commonly flag unsigned Rust binaries that download and install packages.

**To verify your copy is authentic:**

```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Run verification
$uv = "$env:LOCALAPPDATA\iris\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

If attestation says "Verification succeeded" and the last line prints `True`, you're good.

**To whitelist Iris:**
- **Windows Defender:** Run PowerShell as Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\iris\bin"`
- **Bitdefender:** Add an exception in the Bitdefender console (Protection > Antivirus > Settings > Manage Exceptions)
- Whitelist the **folder**, not the file hash — Iris updates `uv` and the hash changes every version

For more context, see the upstream Astral reports: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Getting Started

```bash
iris              # Interactive CLI — start a conversation
iris model        # Choose your LLM provider and model
iris tools        # Configure which tools are enabled
iris config set   # Set individual config values
iris config get   # Print individual config values
iris gateway      # Start the messaging gateway (Telegram, Discord, etc.)
iris setup        # Run the full setup wizard (configures everything at once)
iris claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
iris update       # Update to the latest version
iris doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://gitcode.com/badhope/iris/tree/main/docs)**

---

## Skip the API-key collection — Nous Portal

Iris works with whatever provider you want — that's not changing. But if you'd rather not collect five separate API keys for the model, web search, image generation, TTS, and a cloud browser, **[Nous Portal](https://portal.nousresearch.com)** covers all of them under one subscription:

- **300+ models** — pick any of them with `/model <name>`
- **Tool Gateway** — web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), cloud browser (Browser Use), all routed through your sub. No extra accounts.

One command from a fresh install:

```bash
iris setup --portal
```

That logs you in via OAuth, sets Nous as your provider, and turns on the Tool Gateway. Check what's wired up any time with `iris portal info`. Full details on the [Tool Gateway docs page](../docs/usage.md).

You can still bring your own keys per-tool whenever you want — the gateway is per-backend, not all-or-nothing.

---

## CLI vs Messaging Quick Reference

Iris has two entry points: start the terminal UI with `iris`, or run the gateway and talk to it from Telegram, Discord, Slack, WhatsApp, Signal, or Email. Once you're in a conversation, many slash commands are shared across both interfaces.

| Action                         | CLI                                           | Messaging platforms                                                              |
| ------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Start chatting                 | `iris`                                      | Run `iris gateway setup` + `iris gateway start`, then send the bot a message |
| Start fresh conversation       | `/new` or `/reset`                            | `/new` or `/reset`                                                               |
| Change model                   | `/model [provider:model]`                     | `/model [provider:model]`                                                        |
| Set a personality              | `/personality [name]`                         | `/personality [name]`                                                            |
| Retry or undo the last turn    | `/retry`, `/undo`                             | `/retry`, `/undo`                                                                |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                        |
| Browse skills                  | `/skills` or `/<skill-name>`                  | `/<skill-name>`                                                                  |
| Interrupt current work         | `Ctrl+C` or send a new message                | `/stop` or send a new message                                                    |
| Platform-specific status       | `/platforms`                                  | `/status`, `/sethome`                                                            |

For the full command lists, see the [CLI guide](../docs/usage.md) and the [Messaging Gateway guide](../docs/usage.md).

---

## Documentation

All documentation lives at **[docs/](../docs/)**:

| Section                                                                                             | What's Covered                                             |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [Quickstart](../docs/quickstart.md)                 | Install → setup → first conversation in 2 minutes          |
| [CLI Usage](../docs/usage.md)                              | Commands, keybindings, personalities, sessions             |
| [Configuration](../docs/configuration.md)                | Config file, providers, models, all options                |
| [Messaging Gateway](../docs/usage.md)                | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](../docs/usage.md)                          | Command approval, DM pairing, container isolation          |
| [Tools & Toolsets](../docs/usage.md)            | 40+ tools, toolset system, terminal backends               |
| [Skills System](../docs/usage.md)              | Procedural memory, Skills Hub, creating skills             |
| [Memory](https://gitcode.com/badhope/iris/tree/main/docs)                     | Persistent memory, user profiles, best practices           |
| [MCP Integration](https://gitcode.com/badhope/iris/tree/main/docs)               | Connect any MCP server for extended capabilities           |
| [Cron Scheduling](https://gitcode.com/badhope/iris/tree/main/docs)              | Scheduled tasks with platform delivery                     |
| [Context Files](https://gitcode.com/badhope/iris/tree/main/docs)       | Project context that shapes every conversation             |
| [Architecture](https://gitcode.com/badhope/iris/tree/main/docs)             | Project structure, agent loop, key classes                 |
| [Contributing](https://gitcode.com/badhope/iris/tree/main/docs)             | Development setup, PR process, code style                  |
| [CLI Reference](https://gitcode.com/badhope/iris/tree/main/docs)                  | All commands and flags                                     |
| [Environment Variables](https://gitcode.com/badhope/iris/tree/main/docs) | Complete env var reference                                 |

---

## Migrating from OpenClaw

If you're coming from OpenClaw, Iris can automatically import your settings, memories, skills, and API keys.

**During first-time setup:** The setup wizard (`iris setup`) automatically detects `~/.openclaw` and offers to migrate before configuration begins.

**Anytime after install:**

```bash
iris claw migrate              # Interactive migration (full preset)
iris claw migrate --dry-run    # Preview what would be migrated
iris claw migrate --preset user-data   # Migrate without secrets
iris claw migrate --overwrite  # Overwrite existing conflicts
```

What gets imported:

- **SOUL.md** — persona file
- **Memories** — MEMORY.md and USER.md entries
- **Skills** — user-created skills → `~/.iris/skills/openclaw-imports/`
- **Command allowlist** — approval patterns
- **Messaging settings** — platform configs, allowed users, working directory
- **API keys** — allowlisted secrets (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — workspace audio files
- **Workspace instructions** — AGENTS.md (with `--workspace-target`)

See `iris claw migrate --help` for all options, or use the `openclaw-migration` skill for an interactive agent-guided migration with dry-run previews.

---

## Contributing

We welcome contributions! See the [Contributing Guide](https://gitcode.com/badhope/iris/tree/main/docs) for development setup, code style, and PR process.

Quick start for contributors — use the standard installer, then work from the
full git checkout it creates at `$IRIS_HOME/iris-agent` (usually
`~/.iris/iris-agent`). This matches the layout used by `iris update`, the
managed venv, lazy dependencies, gateway, and docs tooling.

```bash
git clone https://gitcode.com/badhope/iris.git && cd iris/agent && ./setup-iris.sh
cd "${IRIS_HOME:-$HOME/.iris}/iris-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

Manual clone fallback (for throwaway clones/CI where you intentionally do not
want the managed install layout):

Create the venv outside the cloned source tree — a venv inside the directory
the agent operates from can be wiped by a relative-path command the agent runs
against its own checkout, destroying the running runtime mid-session.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.iris/venvs/iris-dev --python 3.11
source ~/.iris/venvs/iris-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Community

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://gitcode.com/badhope/iris/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Linux desktop-control MCP server for Iris and other MCP hosts, with AT-SPI accessibility trees, Wayland/X11 input, screenshots, and compositor window targeting.
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Community WeChat bridge: Run Iris Agent and OpenClaw on the same WeChat account.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).
