# Iris WebUI 环境变量参考

> 本文档只覆盖 **WebUI 侧** 的环境变量（前缀 `IRIS_WEBUI_*` 及少量与之配套的启动开关）。
> Agent 核心侧的变量（`IRIS_HOME`、`IRIS_CONFIG_PATH`、`API_SERVER_KEY`、`IRIS_API_URL`、
> provider 凭证等）见 agent 仓库 / 根目录 `docs/configuration.md`，不在此处重复。
>
> 所有条目均以 `webui/` 当前源码为准（`api/config.py`、`api/startup.py`、`bootstrap.py`、
> `start.sh`、`ctl.sh`、`watchdog.sh`、`docker_init.bash`、`start.ps1`、`api/auth*.py`、
> `api/gateway_chat.py`、`api/runner_client.py`），未在源码中出现的变量不在本表。
>
> 加载顺序速记：`start.sh` / `bootstrap.py` 启动时先把仓库根 `.env` 注入进程环境
> （`IRIS_WEBUI_PRESERVE_ENV=1` 时不覆盖已存在的 shell 变量）；server 运行时再独立加载
> `~/.iris/.env`（provider 凭证用）。shell 环境 > `.env` 文件的覆盖细节见各变量说明。

## 目录

- [1. 启动器与进程生命周期](#1-启动器与进程生命周期)
- [2. 监听地址与 TLS](#2-监听地址与-tls)
- [3. Agent 集成（最常需要手工设置的一组）](#3-agent-集成最常需要手工设置的一组)
- [4. 状态与路径](#4-状态与路径)
- [5. 认证与安全](#5-认证与安全)
- [6. 聊天后端：进程内 / Gateway / 远程 runner](#6-聊天后端进程内--gateway--远程-runner)
- [7. 限额与性能调优](#7-限额与性能调优)
- [8. 上传、附件与媒体快照](#8-上传附件与媒体快照)
- [9. 功能开关与杂项](#9-功能开关与杂项)
- [10. 仅测试用（请勿在生产设置）](#10-仅测试用请勿在生产设置)

---

## 1. 启动器与进程生命周期

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_PRESERVE_ENV` | *(unset)* | 真值（`1/true/yes/on`）时，`bootstrap.py` 加载仓库 `.env` **不覆盖**已存在的 shell 环境变量。`ctl.sh` 自己解析过 `IRIS_HOME`/`IRIS_WEBUI_STATE_DIR` 后会自动置 1，防止 `.env` 把已解析的值冲掉。 |
| `IRIS_WEBUI_NO_DOTENV` | `0`（`ctl.sh` 内判断） | `=1` 时 `ctl.sh` 完全不加载仓库 `.env`。 |
| `IRIS_WEBUI_FOREGROUND` | *(unset)* | 真值时 `bootstrap.py` 以前台模式 `exec` 进 `server.py`（供 systemd / launchd / supervisord 托管），不双 fork、不做健康探针、不自动开浏览器。`--foreground` 命令行参数等价；systemd 的 `INVOCATION_ID`、launchd 的 `XPC_SERVICE_NAME`、supervisord 的 `SUPERVISOR_ENABLED` 等环境出现时会自动提升为前台模式。 |
| `IRIS_WEBUI_LOG_FILE` | `$IRIS_HOME/webui.log` | `ctl.sh` 守护模式写入的日志路径。 |
| `IRIS_WEBUI_LOG_DIR` | state 目录 | server 运行日志目录。 |
| `IRIS_WEBUI_PID_FILE` | `$IRIS_HOME/webui.pid` | `ctl.sh` 记录守护进程 PID 的文件。 |
| `IRIS_WEBUI_LOCK_FILE` / `IRIS_WEBUI_CTL_STATE_FILE` | ctl 内部默认 | `ctl.sh` 的单实例锁 / 状态文件，一般无需手工设置。 |
| `IRIS_WEBUI_START_GRACE` | `3` 秒 | `ctl.sh start` 后等待 server 起来的宽限秒数。 |
| `IRIS_WEBUI_STARTUP_GRACE_SECONDS` | `2` 秒 | WSL 自启动脚本 `scripts/wsl/iris_webui_autostart.sh` 用：nohup 拉起 `start.sh` 后、首次探 `/health` 之前的等待秒数。探针结果分三类——已健康 / 进程在但尚未就绪 / 启动后即退出。与上面 `IRIS_WEBUI_START_GRACE`（`ctl.sh`）是两个独立启动器的变量，互不影响。 |
| `IRIS_WEBUI_WATCHDOG_LOG` | `$IRIS_HOME/webui.watchdog.log` | `watchdog.sh` 自身日志。 |
| `IRIS_WEBUI_CTL_ALLOW_PORT_CONFLICT` / `IRIS_WEBUI_CTL_ALLOW_SYSTEMD_CONFLICT` / `IRIS_WEBUI_CTL_ALLOW_LAUNCHD_CONFLICT` | *(unset)* | `ctl.sh` 在端口占用 / systemd unit 冲突 / launchd plist 冲突时的放行开关。 |
| `IRIS_WEBUI_SYSTEMD_UNIT` / `IRIS_WEBUI_LAUNCHD_LABEL` | 自动推断 | 托管集成时使用的 unit 名 / Label 覆盖。 |
| `IRIS_WEBUI_SERVER_CWD` | agent 目录（无 agent 时为 webui 仓库根） | server 进程的工作目录。agent 目录只读时把它指到可写 workspace，避免相对路径兜底写崩。 |
| `IRIS_WEBUI_REPO` | webui 仓库根（`bootstrap.py` 所在目录） | 仓库根覆盖，一般不需要。 |

## 2. 监听地址与 TLS

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_HOST` | `127.0.0.1` | 绑定地址。`0.0.0.0` 所有 IPv4、`::` 所有 IPv6、`::1` IPv6 回环。 |
| `IRIS_WEBUI_PORT` | `8787` | 监听端口；位置参数（`./start.sh 9000`）覆盖 env。 |
| `IRIS_WEBUI_TLS_CERT` | *(unset)* | 证书 PEM 路径。与 `IRIS_WEBUI_TLS_KEY` **同时设置**才启用 HTTPS；两者任一缺失即回退 HTTP。 |
| `IRIS_WEBUI_TLS_KEY` | *(unset)* | 私钥 PEM 路径。 |
| `IRIS_WEBUI_TLS_INSECURE_PROBE` | *(unset)* | `=1` 时健康探针跳过证书校验、静默继续（自签证书托管场景）。 |
| `IRIS_WEBUI_PROBE_SCHEME` | 自动（按 TLS 配置） | 探针强制使用的 scheme。 |
| `IRIS_WEBUI_HEALTH_URL` / `IRIS_WEBUI_HEALTH_URL_EXPLICIT` / `IRIS_WEBUI_HEALTH_HOST` | 由 host:port 推导 | `ctl.sh` / watchdog 健康探针 URL 覆盖。 |

## 3. Agent 集成（最常需要手工设置的一组）

WebUI 默认把 Iris Agent **跑在同一进程内**（in-process），运行时 `api/config.py` 会把
`IRIS_WEBUI_AGENT_DIR` append 进 `sys.path` 再 `from run_agent import AIAgent`。
因此要求：**运行 server 的那个 Python 解释器里同时装好 WebUI 依赖与 Agent 依赖**。

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_AGENT_DIR` | 自动发现（见下） | Iris Agent 源码 / 安装根目录（含 `run_agent.py`）。**显式设置永远最高优先级**。自动发现顺序：本变量 → `$IRIS_HOME/iris-agent` → webui 仓库同级 `../iris-agent` → webui 父目录本身（嵌套布局）→ `~/.iris/iris-agent` → `~/iris-agent` → `$XDG_DATA_HOME/iris-agent` → `/opt/iris-agent`、`/usr/local/iris-agent`、`/usr/local/share/iris-agent` → PATH 上 `iris` 启动器反推 → `IRIS_WEBUI_PYTHON` 能 import 到的 `run_agent`。 |
| `IRIS_WEBUI_PYTHON` | 自动发现 | 显式指定运行 server 的解释器。优先级：本变量 → agent venv（`<agent_dir>/venv/bin/python`、`.venv/bin/python`、Windows 对应 `Scripts/`）→ webui 仓库 `.venv` → 系统 `python3`。**排障首选**：agent 依赖装在哪个解释器就把它指过去。 |
| `IRIS_WEBUI_DISABLE_LOCAL_VENV` | *(unset)* | 真值时，`bootstrap.py` 在找不到“能同时 import WebUI 依赖 + `run_agent`”的解释器后**拒绝自动创建 webui/.venv** 并直接报错（打包/托管镜像场景用）。 |
| `IRIS_WEBUI_AUTO_INSTALL` | *(unset，关闭)* | 真值（`1/true/yes`）时，server 启动阶段允许自动 `pip install` agent 的 `requirements.txt` 到当前解释器；且 agent 目录需通过“属主=当前用户且不可 group/other 写”的信任检查。未开启时只打印提示不安装。 |
| `IRIS_WEBUI_RUNTIME_ADAPTER` | `legacy-direct` | agent 运行时适配。`legacy-direct`（默认，直接 journal 内存态）；`legacy-journal` 走落盘 journal 回放路径。 |
| `IRIS_WEBUI_REQUIRE_AGENT_PROCESS` | *(unset)* | 真值时要求独立 agent 进程存在，否则启动失败。 |
| `IRIS_WEBUI_DEFAULT_WORKSPACE` | `~/workspace` | 首次进入时默认打开的工作区目录；不存在时回退 state 目录。容器入口默认置为 `/workspace`。 |
| `IRIS_WEBUI_DEFAULT_MODEL` | *(unset，用 provider 默认)* | 可选模型覆盖；留空使用当前 provider 默认模型（避免向非 OpenAI 用户展示不可用模型）。 |
| `IRIS_WEBUI_BOT_NAME` | `Iris` | 界面显示的 bot 名称。 |
| `IRIS_WEBUI_CLAUDE_PROJECTS_DIR` | *(unset)* | 对接 Claude projects 目录。 |

> **本地从源码跑通的实测前提**：webui 仓库 `.venv` 里必须同时具备 WebUI 依赖
> （`pip install -r webui/requirements.txt`，即 pyyaml + cryptography）和 Agent 依赖。
> 两条等价路径任选其一：
> 1. 在 webui `.venv` 中 `pip install -e ./agent`（连带装好 agent 依赖），并
>    `export IRIS_WEBUI_AGENT_DIR=/…/iris/agent`；
> 2. 直接 `export IRIS_WEBUI_PYTHON=/path/to/agent/venv/bin/python`（agent venv 里补装
>    webui requirements）。
> 详见 [`DEPLOYING.md`](DEPLOYING.md) 与根 README Quick Start。

## 4. 状态与路径

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_STATE_DIR` | `$IRIS_HOME/webui`（POSIX `~/.iris/webui`；Windows `%LOCALAPPDATA%\iris\webui`） | 会话、JSON sidecar、运行态等一切 webui 私有状态根。**升级注意**：默认跟随 `IRIS_HOME`；若历史上挪过 `IRIS_HOME` 又没显式设本变量，需手动把旧目录指回来。 |
| `IRIS_WEBUI_ISOLATED_PROFILE` | *(unset)* | profile 隔离模式开关。 |
| `IRIS_WEBUI_PLUGINS_DIR` | `~/.iris/plugins` | 插件安装目录。 |
| `IRIS_WEBUI_EXTENSION_DIR` | *(unset)* | 本地扩展目录，经 `/extensions/` 对外静态服务；目录必须在启用前存在。 |
| `IRIS_WEBUI_EXTENSION_MANIFEST` | *(unset)* | `IRIS_WEBUI_EXTENSION_DIR` 内的相对 JSON 清单文件名，声明注入的脚本/样式；见 `docs/EXTENSIONS.md`。 |
| `IRIS_WEBUI_EXTENSION_SCRIPT_URLS` / `IRIS_WEBUI_EXTENSION_STYLESHEET_URLS` | *(unset)* | 逗号分隔的同源脚本 / 样式 URL，追加在清单注入之后。 |
| `IRIS_WEBUI_ATTACHMENT_DIR` | state 目录内默认收件箱 | 聊天上传附件落盘目录（按会话隔离）。 |
| `IRIS_WEBUI_MEDIA_SNAPSHOT_DIR` | state 目录内默认位置 | 媒体快照存储目录。 |
| `IRIS_WEBUI_MEDIA_SNAPSHOT_CAP_BYTES` / `IRIS_WEBUI_MEDIA_SNAPSHOT_MAX_FILE_BYTES` | 内置默认 | 快照总量上限 / 单文件上限。 |
| `IRIS_WEBUI_LOG_FILE` / `IRIS_WEBUI_LOG_DIR` | 见 §1 / state 目录 | 日志落点。 |

## 5. 认证与安全

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_PASSWORD` | *(unset)* | 设置后启用密码登录。**未设置时**仅当绑定 loopback 才允许开放访问；绑到 `0.0.0.0` 而无密码会拒绝启动。 |
| `IRIS_WEBUI_PASSKEY` | *(unset)* | `=1` 启用 passkey / WebAuthn 登录。 |
| `IRIS_WEBUI_SESSION_TTL` | 内置默认（秒） | 登录会话 cookie 有效期。 |
| `IRIS_WEBUI_COOKIE_NAME` | 内置默认名 | 会话 cookie 名；多实例共存时改名避免串站。 |
| `IRIS_WEBUI_PROFILE_COOKIE_NAME` | 内置默认名 | 按 profile 区分的 cookie 名。 |
| `IRIS_WEBUI_SECURE` | 自动 | `1/true/yes` 强制 cookie `Secure`；`0/false/no` 关闭；不设置时按请求 scheme 自动判断。 |
| `IRIS_WEBUI_OIDC_ISSUER` / `IRIS_WEBUI_OIDC_CLIENT_ID` / `IRIS_WEBUI_OIDC_CLIENT_SECRET` / `IRIS_WEBUI_OIDC_REDIRECT_URI` / `IRIS_WEBUI_OIDC_SCOPES` / `IRIS_WEBUI_OIDC_ALLOW_CLAIM` / `IRIS_WEBUI_OIDC_ALLOW_VALUES` | *(unset)* | OIDC 登录全套。issuer + client_id 齐备才启用；`ALLOW_CLAIM`/`ALLOW_VALUES` 限定允许登录的 claim 取值。 |
| `IRIS_WEBUI_TRUSTED_AUTH_HEADER` / `IRIS_WEBUI_TRUSTED_GROUPS_HEADER` / `IRIS_WEBUI_GROUP_PROFILE_MAP` / `IRIS_WEBUI_TRUSTED_AUTH_LOGOUT_URL` / `IRIS_WEBUI_TRUSTED_GROUPS_PIPE_SEPARATOR` | *(unset)* | 反向代理受信任头 SSO：从指定请求头取用户名 / 组；`GROUP_PROFILE_MAP` 是 JSON 映射组→profile；`=1` 时组头额外按 `|` 切分。 |
| `IRIS_WEBUI_TRUSTED_PROXY_CIDRS` | *(unset)* | 逗号分隔的 CIDR 白名单；只有来自这些网段的代理才被允许投递 `X-Forwarded-*`。 |
| `IRIS_WEBUI_TRUST_FORWARDED_FOR` / `IRIS_WEBUI_TRUST_FORWARDED_HOST` / `IRIS_WEBUI_TRUST_FORWARDED_PROTO` | *(unset)* | 真值才信任对应 `X-Forwarded-*` 头。默认不信任——裸客户端伪造这些头不会被采纳。 |
| `IRIS_WEBUI_ALLOWED_ORIGINS` | *(unset)* | 逗号分隔的额外 CORS 允许来源（如 `https://app.example.com:8000`），反代 / 嵌入式场景用。 |
| `IRIS_WEBUI_CSP_CONNECT_EXTRA` / `IRIS_WEBUI_CSP_FRAME_EXTRA` | *(unset)* | 追加进 CSP `connect-src` / `frame-src` 的额外 `http(s)://`、`ws(s)://` 源（反代、隧道、扩展 sidecar、内嵌 dashboard）。 |
| `IRIS_WEBUI_ONBOARDING_OPEN` | *(unset)* | `=1` 允许在非 localhost、未开认证的服务器上跑 onboarding 向导（默认远程直接禁用，防裸奔）。 |
| `IRIS_WEBUI_SKIP_ONBOARDING` | *(unset)* | 真值（`1/true/yes`）无条件跳过首次向导（托管 / 已预置配置场景）。 |

## 6. 聊天后端：进程内 / Gateway / 远程 runner

默认 `legacy`：WebUI **进程内**直接跑 agent（读 `IRIS_HOME` 配置）。`IRIS_API_URL` 只供
Tasks/cron 健康探针使用，**不**路由聊天。

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_CHAT_BACKEND` | `legacy`（进程内） | `gateway`（别名 `api_server`/`api-server`）改为把聊天转发给独立的 Iris Gateway API server。 |
| `IRIS_WEBUI_GATEWAY_BASE_URL` | *(unset)* | Gateway 地址，如 `http://127.0.0.1:8642`。 |
| `IRIS_WEBUI_GATEWAY_API_KEY` | *(unset)* | 与 Gateway 侧 `API_SERVER_KEY` **同一个值**（容器 compose 中由 `API_SERVER_KEY` 自动转发派生）。不匹配时健康探针/聊天直接报错并给出排障提示。 |
| `IRIS_WEBUI_GATEWAY_READ_TIMEOUT` | `600` 秒 | Gateway SSE 套接字的“总字节静默预算”：窗口内任意字节都不算超时；超过即判定死连接并响应 Stop。想更激进的死连接熔断可调小。 |
| `IRIS_WEBUI_GATEWAY_USE_RUNS_API` | *(unset)* | 真值时走 Gateway 的 `/v1/runs` 运行接口而非旧聊天接口。 |
| `IRIS_WEBUI_RUNNER_BASE_URL` | *(unset)* | 配置后 WebUI 仅作前端，实际聊天委托给外部 HTTP runner（`POST /v1/runs`）；只允许 http(s) scheme。 |
| `IRIS_WEBUI_RUNNER_API_KEY` | *(unset)* | 调用 runner 时带的 bearer key。 |

## 7. 限额与性能调优

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_VISIBLE_SESSION_LIMIT` | `20`（上限钳到 200） | 侧栏最近会话窗口大小；同时约束 delegated subagent 嵌套深度。非整数 / 非正数回退默认。在 profile 初始化前解析，profile `.env` 改不动。 |
| `IRIS_WEBUI_SESSIONS_MAX` | 约 `100`（跟随内置 cache 默认） | 内存中紧凑 `Session` 对象 LRU 上限的旧版 env 覆盖；优先用 `config.yaml` 的 `webui.sessions_cache_max`。只淘汰干净、已持久化、非活跃的会话。 |
| `IRIS_WEBUI_AGENT_CACHE_MAX` | `25` | 内存中热保留的 agent 实例 LRU 上限，每个实例钉住完整对话 transcript——驻留内存的主要杠杆。 |
| `IRIS_WEBUI_MODELS_REBUILD_BUDGET` | `4` | 模型列表重建预算；`=0` 回退旧的同步重建。 |
| `IRIS_WEBUI_BUDGET_WARN_COOLDOWN` | `300` 秒 | 预算告警冷却。 |
| `IRIS_WEBUI_MAX_SESSION_RESOLVE` | 内置默认 | 会话解析并发/数量上限。 |
| `IRIS_WEBUI_LINEAGE_TOP_N` | `300` | session lineage 查询返回条数上限。 |
| `IRIS_WEBUI_STATE_DB_OVERRIDE_TOP_N` | `300` | state DB 查询条数覆盖。 |
| `IRIS_WEBUI_SLOW_REQUEST_SECONDS` | *(unset)* | 慢请求诊断阈值（秒），超过即记录诊断日志。 |
| `IRIS_WEBUI_STALE_COMPLETION_MAX_AGE_SECONDS` | *(unset)* | 判定“陈旧完成态”的最大年龄。 |
| `IRIS_WEBUI_SSE_CHUNKED` | *(unset)* | 真值时 SSE 用 `Transfer-Encoding: chunked`。在会缓冲整条流的反代（如 jupyter-server-proxy）后必须开；直连无害。 |
| `IRIS_WEBUI_SSE_WRITE_DEADLINE` | *(unset)* | SSE 写出截止时间（兼容旧 `IRIS_SSE_WRITE_DEADLINE`）。 |
| `IRIS_WEBUI_STREAM_WRITEBACK_DIAG_MS` | *(unset)* | 流式写回诊断打点阈值（毫秒）。 |
| `IRIS_WEBUI_RUN_JOURNAL_FSYNC` | *(unset)* | run journal 写盘后是否 fsync。 |
| `IRIS_WEBUI_PREFILL_MESSAGES_SCRIPT` / `IRIS_WEBUI_PREFILL_MESSAGES_SCRIPT_TIMEOUT` / `IRIS_WEBUI_PREFILL_CONTEXT_MAX_CHARS` | 见 config.yaml 对应键 | 动态会话召回 prefill：自定义脚本命令 / 超时 / 上下文截断字符数；详见 `docs/advanced-chat-setup.md`。 |
| `IRIS_WEBUI_EXTERNAL_NOTES_SOURCES` | *(unset)* | 真值时允许外部笔记源（Joplin/Obsidian/Notion 等）。 |
| `IRIS_WEBUI_WORKSPACE_GIT_DESTRUCTIVE` | *(unset)* | 放行 workspace-git 的破坏性操作。 |

## 8. 上传、附件与媒体快照

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_MAX_UPLOAD_MB` | `20` | 单次上传体积上限（MB）。 |
| `IRIS_WEBUI_MAX_EXTRACTED_MB` | 内置默认 | 上传压缩包解压后总体积上限（MB）。 |
| `IRIS_WEBUI_FOLDER_ZIP_MAX_MB` | `1024` | 文件夹打包下载体积上限（MB）。 |
| `IRIS_WEBUI_FOLDER_ZIP_MAX_FILES` | `50000` | 文件夹打包下载文件数上限。 |

## 9. 功能开关与杂项

| 变量 | 默认值 | 作用与语义 |
|---|---|---|
| `IRIS_WEBUI_SELF_SIGNED_WARNED` | *(unset)* | 自签证书告警去重标记（内部）。 |
| `IRIS_WEBUI_TERMINAL` | *(unset)* | 内嵌终端能力标记。 |
| `IRIS_WEBUI_ONBOARDING_OPEN` | 见 §5 | 远程开放 onboarding。 |

## 10. 仅测试用（请勿在生产设置）

下列变量只被 `tests/` 与 pytest 夹具引用，生产环境设置会污染行为或无意义：
`IRIS_WEBUI_TEST_STATE_DIR`、`IRIS_WEBUI_TEST_PYTHON`、`IRIS_WEBUI_TEST_NETWORK_BLOCK`、
`IRIS_WEBUI_FOREGROUND`（作为人工开关时见 §1）。

---

## 配套（非 `IRIS_WEBUI_*`，但 webui 启动必读）

| 变量 | 默认 | 说明 |
|---|---|---|
| `IRIS_HOME` | POSIX `~/.iris`；Windows `%LOCALAPPDATA%\iris` | Iris 状态根，派生 `STATE_DIR`、agent 候选目录、`config.yaml` 位置。 |
| `IRIS_CONFIG_PATH` | `$IRIS_HOME/config.yaml` | agent 配置文件路径。 |
| `API_SERVER_KEY` | *(unset)* | Gateway/agent API server 的 bearer key（≥16 字符，短了被 agent 静默忽略）；compose 中 WebUI 自动把它转发为 `IRIS_WEBUI_GATEWAY_API_KEY`。 |
| `IRIS_API_URL` / `GATEWAY_HEALTH_URL` | `http://127.0.0.1:8642[/health]` | Tasks/cron 健康探针用，**不路由聊天**。 |
