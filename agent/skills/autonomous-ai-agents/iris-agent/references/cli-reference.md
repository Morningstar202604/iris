# Iris CLI Reference

Live sources when anything looks stale: `iris --help`, `iris <command> --help`,
https://gitcode.com/badhope/iris/tree/main/docs

### Global Flags

```
iris [flags] [command]        (no subcommand = interactive chat)

  --version, -V             Show version
  -z, --oneshot PROMPT      One-shot: print ONLY the final response (for scripts/pipes)
  -m MODEL  --provider P    Model/provider override for this invocation
  -t, --toolsets LIST       Comma-separated toolsets for this invocation
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --tui / --cli             Force the Ink TUI / classic REPL
  --ignore-rules            Skip AGENTS.md/SOUL.md/memory/skill injection
  --safe-mode               Disable ALL customizations (troubleshooting)
  --pass-session-id         Include session ID in system prompt
```

### Chat

```
iris chat [flags]
  -q, --query TEXT          Single query, non-interactive
  --image PATH              Attach a local image to a single query
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --max-turns N             Cap tool-calling iterations
  --source TAG              Session source tag (default: cli)
```
(plus the global flags above)

### Configuration

```
iris setup [section]      Wizard (model|tts|terminal|gateway|tools|agent)
iris model                Interactive model/provider picker
iris fallback [add|remove|list]  Fallback provider chain
iris config [show|edit|get|set|unset|path|env-path|check|migrate]
iris login / logout       OAuth sign-in / clear stored auth
iris doctor [--fix]       Check dependencies and config
iris status [--all]       Component status
```

### Tools & Skills

```
iris tools [list|enable NAME|disable NAME]   Per-platform toolsets (curses UI with no args)

iris skills list|browse|search QUERY|inspect ID
iris skills install ID    Hub identifier OR a direct https://…/SKILL.md URL
iris skills config        Enable/disable skills per platform
iris skills check|update|uninstall|publish PATH
iris skills tap add REPO  Add a GitHub repo as a skill source
iris bundles              Skill bundles (one /<name> alias loads several skills)
```

### MCP Servers

```
iris mcp add NAME (--url or --command) | remove | list | test NAME
iris mcp catalog | install NAME     Curated catalog install
iris mcp configure NAME             Toggle tool selection
iris mcp serve                      Run Iris as an MCP server
```
Details (transport, tool discovery, catalog): `references/native-mcp.md`.

### Gateway (Messaging Platforms)

```
iris gateway run|install|start|stop|restart|status|setup
```

20+ platforms: Telegram, Discord, Slack, WhatsApp (Baileys + Business Cloud API), iMessage (Photon — `iris photon setup`), Signal, Email, SMS, Matrix, Mattermost, Teams, LINE, SimpleX, ntfy, Google Chat, Home Assistant, DingTalk, Feishu, WeCom, Weixin, API Server, Webhooks. Open WebUI connects via the API Server adapter. Most adapters ship under `plugins/platforms/`.
Docs: https://gitcode.com/badhope/iris/tree/main/docs

### Sessions

```
iris sessions list|browse|rename ID TITLE|delete ID|export OUT|prune|stats
```

### Cron / Webhooks

```
iris cron list|create SCHED|edit ID|pause|resume|run ID|remove|status
    Schedules: '30m', 'every 2h', '0 9 * * *', ISO timestamp
iris webhook subscribe NAME|list|remove NAME|test NAME
```
Webhook payloads/routes: `references/webhooks.md`.

### Profiles

```
iris profile list|create NAME (--clone|--clone-all|--clone-from)|use|show|delete
iris profile rename A B | alias NAME | export NAME | import FILE
iris profile migrate-identity A B   Retry a completed rename's session/routing identity migration
```

### Credentials & Pools

```
iris auth                 Interactive credential manager
iris auth add [PROVIDER]  Add OAuth or API-key credential (nous, openai-codex, qwen-oauth, …)
iris auth list|remove P IDX|reset PROVIDER|status
```
Multiple credentials per provider form a pool that rotates automatically and skips exhausted keys.

### Other

```
iris desktop / gui        Native desktop app
iris dashboard            Web admin panel + embedded chat (--stop / --status)
iris proxy                OpenAI-compatible local proxy backed by an OAuth provider
iris portal               Quick setup / sign in via Nous Portal
iris kanban <verb>        Multi-agent work-queue board
iris project              Named multi-folder workspaces
iris skin list|use|set    Switch/tweak skins (see references/themes.md)
iris pets <verb>          Pet mascots (see references/petdex.md)
iris memory setup|status|off|reset   Memory provider
iris secrets bitwarden|onepassword   External secret stores
iris moa                  Mixture-of-Agents slots
iris hooks / security / backup / import / checkpoints / console
iris logs [-f] [errors]   View agent/error logs
iris send                 One-off message through a gateway platform
iris pairing / plugins / insights / journey / computer-use
iris acp                  ACP server (IDE integration)
iris completion bash|zsh|fish
iris update / uninstall / claw migrate
```

Plugin- and provider-supplied subcommands (e.g. `iris photon setup`) only appear once their plugin is installed/active.

### Where to Find Things

| Looking for... | Location |
|---|---|
| Config options | `iris config edit` · [Configuration docs](https://gitcode.com/badhope/iris/tree/main/docs) |
| Tools / toolsets | `iris tools list` · [Tools reference](https://gitcode.com/badhope/iris/tree/main/docs) |
| Skills catalog | `iris skills browse` · [Skills catalog](https://gitcode.com/badhope/iris/tree/main/docs) |
| Provider setup | `iris model` · [Providers guide](https://gitcode.com/badhope/iris/tree/main/docs) |
| Env variables | `iris config env-path` · [Env vars reference](https://gitcode.com/badhope/iris/tree/main/docs) |
| Gateway logs | `~/.iris/logs/gateway.log` (or `iris logs`) |
| Sessions | `iris sessions browse` (reads state.db) |
