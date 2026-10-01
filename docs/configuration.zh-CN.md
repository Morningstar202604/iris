# Configuration Reference

[English](configuration.md) · **简体中文**


Iris 的运行时配置位于 `$IRIS_HOME/config.yaml`（首次启动自动创建）。
默认 `$IRIS_HOME` 在 Linux/macOS 为 `~/.iris`，Windows 为 `%LOCALAPPDATA%\iris`。
本文档覆盖公开使用最相关的配置块。全部设置项可在 Web UI **设置**页完成，配置文件的优先级最高。

> 权威、带完整注释的源文件：`agent/cli-config.yaml.example`。
> 下文默认值均提取自该文件与 `agent/iris_cli/config_defaults.py`，**不要自行编造键名**。

## 磁盘文件布局

```
~/.iris/
├── config.yaml          # 运行时配置（即本文件）
├── .env                 # API 密钥与敏感环境变量（chmod 600）
├── auth.json            # OAuth 会话令牌（Codex、Nous 等）
├── active_profile       # 当前 sticky-active 的命名 profile 名
├── state.db             # 会话、消息、工具调用、FTS5 全文索引
├── SOUL.md              # Agent 人格 / system prompt
├── cron/  sessions/  logs/  memories/  pairing/  hooks/
├── image_cache/  audio_cache/  skills/
└── profiles/<name>/     # 命名 profile 各自的独立目录
```

- **Profiles（多配置档）**：默认 profile 就是 `~/.iris` 本身；命名 profile 放在
  `~/.iris/profiles/<name>/`，各自携带独立的 `config.yaml`、`.env`、`state.db`。
  用 `iris profile use <name>` 切换，激活名写入 `~/.iris/active_profile`。
- 直接编辑 YAML，或用 `iris config set <section.key> <value>` 修改。

## model — 主模型

```yaml
model:
  default: "anthropic/claude-opus-4.6"  # 默认模型（"model:" 是等价别名）
  provider: "auto"                       # 提供商 ID（见下表）
  base_url: "https://openrouter.ai/api/v1"
  # api_key: "your-key-here"             # 可选；缺省回退到对应环境变量
  # streaming: true                      # false = 整段会话强制非流式
  # context_length: 131072              # 总上下文窗口；不设则自动探测
```

| `provider` 取值 | 含义 | 所需凭证 |
|---|---|---|
| `auto` | 按已有凭证自动探测（**默认**） | — |
| `openrouter` | OpenRouter | `OPENROUTER_API_KEY` 或 `OPENAI_API_KEY` |
| `nous` / `nous-api` | Nous Portal（OAuth / API key） | `iris auth add nous` / `NOUS_API_KEY` |
| `anthropic` | Anthropic 直连 | `ANTHROPIC_API_KEY` |
| `openai-codex` | OpenAI Codex（OAuth） | `iris auth add openai-codex` |
| `copilot` | GitHub Copilot / GitHub Models | `GITHUB_TOKEN` |
| `gemini` | Google AI Studio 直连 | `GOOGLE_API_KEY` 或 `GEMINI_API_KEY` |
| `zai` | z.ai / 智谱 GLM | `GLM_API_KEY` |
| `kimi-coding` | Kimi / Moonshot | `KIMI_API_KEY` |
| `minimax` / `minimax-cn` | MiniMax 国际 / 国内 | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` |
| `huggingface` | Hugging Face Inference | `HF_TOKEN` |
| `nvidia` | NVIDIA NIM | `NVIDIA_API_KEY` |
| `xiaomi` | 小米 MiMo | `XIAOMI_API_KEY` |
| `arcee` | Arcee AI Trinity | `ARCEEAI_API_KEY` |
| `ollama-cloud` | Ollama Cloud | `OLLAMA_API_KEY` |
| `deepinfra` | DeepInfra | `DEEPINFRA_API_KEY` |
| `kilocode` | KiloCode 网关 | `KILOCODE_API_KEY` |
| `ai-gateway` | Vercel AI Gateway | `AI_GATEWAY_API_KEY` |
| `azure-foundry` | Azure OpenAI / Foundry | API key 或 Entra ID |
| `lmstudio` | LM Studio 本地服务 | 可选 `LM_API_KEY`（默认 `http://127.0.0.1:1234/v1`） |
| `custom` | 任意 OpenAI 兼容端点（需设 `base_url`） | `base_url` + 密钥 |

`ollama`、`vllm`、`llamacpp` 都是 `custom` 的别名。

- `context_length`（可选）：总上下文窗口（输入+输出合计）。仅在自动探测不准时
  手动设置（如本地服务自定义了 `num_ctx`，或代理不暴露 `/v1/models`）。
- `ollama_num_ctx`：仅 Ollama，每次请求发送的 `num_ctx`；显式设置后原样发送、不被截断。
- `default_headers` / `extra_headers`：每次 OpenAI 线请求附加的 HTTP 头
  （用于在网关/WAF 后覆盖 SDK 默认 `User-Agent`）。两者都设时 `extra_headers` 胜出。

### providers: — 命名提供商级覆盖

```yaml
providers:
  my-proxy:
    base_url: "https://llm.internal.example.com/v1"
    api_key: "${MY_PROXY_API_KEY}"   # 或 key_env: MY_PROXY_API_KEY
    extra_headers:
      X-Client-Name: "iris-agent"
    request_timeout_seconds: 300     # 该提供商的请求超时
    stale_timeout_seconds: 900       # 非流式卡死探测
    models:                          # 按模型例外
      claude-opus-4.6:
        timeout_seconds: 600
```

- `key_cmd`：一个**打印**新短期令牌的命令，每次请求执行（临期前缓存）——
  用于 SSO/OIDC/IAM 短期 bearer。优先级：`--api-key` > `key_cmd` > 内联 `api_key` / `key_env`。
- `extra_body`：合并到该提供商每次请求的字典（如网关自己的 `service_tier: priority`）。
- `session_affinity_header`：每次请求携带会话 id 的请求头名，用于会话感知代理。

### custom_providers — 模型选择器里的端点分组

```yaml
custom_providers:
  - name: agnes                    # 模型选择器里显示的分组名
    base_url: https://your-endpoint/v1
    api_key: your-key              # 或：key_env: MY_API_KEY_ENV
    models:
      - model-a
      - model-b
```

- 接入后，Web UI 的模型下拉会显示该分组及其模型。
- `key_env: MY_API_KEY_ENV` 从环境变量读密钥，不必写进文件。

### fallback_providers — 故障转移链

当主提供商因瞬时故障（5xx、overloaded/529、连接/读取超时）报错时，Iris 会按此链依次尝试。

```yaml
fallback_providers:
  - provider: "openrouter"
    model: "deepseek/deepseek-chat"
    # base_url: "https://..."      # 可选，自定义端点
    # api_key: "sk-..."            # 可选；否则用 key_env:
```

- 每条需要 `provider` + `model`。旧的 `fallback_model`（单个 dict）仍会合并到
  `fallback_providers` 之后。
- 显式 `[]` 关闭故障转移。

## plugins — 插件

```yaml
plugins:
  enabled:
    - web-defuddle          # 网页正文提取
    - web-knowledge-base    # 知识库搜索
    - image_gen/openai      # 画图后端（openai 兼容端点）
  disabled: []
```

插件按 `类型/名称` 引用（如 `image_gen/openai`）。`plugins.enabled` 是白名单——
未列出的插件不加载。其他可选键：`plugins.hook_callback_timeout`（默认 `30` 秒）、
`plugins.load_timeout_seconds`（默认 `10` 秒）。

## image_gen — 画图

```yaml
image_gen:
  provider: openai          # 画图后端
  openai:
    provider: agnes         # 复用 custom_providers 的端点/密钥
    model: your-image-model # 端点自己的图像模型名（原样透传）
```

- `image_gen.openai.provider` 指向 `custom_providers` 里的名字，自动继承其 base_url 与 api_key。
- 未配置时 `image_generate` 工具不可用（工具列表会隐藏它）。
- 其他插件（`deepinfra` 等）各自读 `image_gen.<name>` 块；`deepinfra` 从目录实时发现模型。

## approvals — 审批

```yaml
approvals:
  mode: smart               # manual | smart | off
  timeout: 300              # 等待人工审批的超时秒数（默认）
  cron_mode: deny           # deny | approve —— cron 任务遇到危险命令时
  single_query_mode: deny    # deny | approve —— `-q` 单次会话
  unattended_mode: deny      # deny | approve —— webhook / api_server 等无人值守面
```

| 模式 | 行为 |
|---|---|
| `manual` | 所有脚本类工具都等人批准（**无人值守任务会超时**） |
| `smart` | 安全命令由守护 LLM 自动放行；危险命令才询问（**推荐**） |
| `off` | 全部自动执行（仅信任脚本时使用） |

Web UI / API 无人值守运行长任务时，建议 `smart`，否则 `execute_code` 等工具会一直等到
`timeout` 超时。其他键：`approvals.deny`（即使 `off` 也阻断的 fnmatch 通配）、
`approvals.smart_policy`（附加守护规则）、`approvals.denial_breaker_threshold`（默认 `3`）。

## terminal — 命令执行后端

```yaml
terminal:
  backend: "local"          # local | ssh | docker | singularity | modal | daytona
  cwd: "."                  # "." = 启动目录（local）；容器/远端时为内部路径
  timeout: 180              # 单命令超时（秒）
  lifetime_seconds: 300     # shell/容器最大空闲存活时间
  home_mode: "auto"         # auto | real | profile —— 工具子进程的 HOME 策略
  docker_mount_cwd_to_workspace: false   # 安全：默认关，需显式开启
```

容器后端（`docker`/`singularity`/`modal`/`daytona`）还支持：
`container_cpu`（默认 `1`）、`container_memory`（默认 `5120` MB）、
`container_disk`（默认 `51200` MB）、`container_persistent`（默认 `true`），
以及各后端专属键（`docker_image`、`ssh_host`/`ssh_user`/`ssh_port`/`ssh_key`、
`singularity_image`、`modal_image`、`daytona_image` 等）。完整参考见
`agent/cli-config.yaml.example`。

## agent — Agent 循环行为

```yaml
agent:
  max_turns: 500                  # 每轮对话最大工具调用迭代数
  verbose: false                  # 详细日志
  reasoning_effort: "medium"      # xhigh | high | medium | low | minimal | none
  reasoning_overrides: {}         # 按模型覆盖思考强度
  service_tier: ""                # ""/normal | fast | auto | cold（一方快通道）
  fast_auto_seconds: 60
  personalities: {}               # 自定义 / 覆盖内置人格
  api_max_retries: 3              # Iris 层 API 错误重试次数
  auto_recovery_cycles: 5         # 瞬时故障的额外抖动重试轮数
```

## compression — 上下文自动压缩

```yaml
compression:
  enabled: true
  threshold: 0.50                 # 占用 context_length 多少比例时触发
  threshold_tokens: 256000        # 触发的绝对 token 上限
  target_ratio: 0.20              # 保留为近期尾部的比例
  protect_last_n: 20              # 始终保留的最近消息数
  protect_first_n: 3              # 始终保留的头部消息数
  max_attempts: 3                 # 压缩失败重试轮数
  checkpoint_required: false       # 无记忆提供者检查点时拒绝有损压缩
```

上下文窗口 < 512K 的模型触发比例下限为 `0.75`（只升不降）。

## memory — 持久记忆

```yaml
memory:
  memory_enabled: true            # Agent 笔记（MEMORY.md）
  user_profile_enabled: true       # 用户画像（USER.md）
  memory_char_limit: 2200          # 约 800 token
  user_char_limit: 1375            # 约 500 token
  nudge_interval: 10              # 每 N 轮提醒 Agent 保存记忆（0 = 关）
```

## skills、toolsets 与 MCP

- **skills**：`skills.creation_nudge_interval`（默认 `15`）、`skills.external_dirs`
  （只读的额外技能目录）。
- **platform_toolsets**：按平台配置工具白名单。默认预设：
  `cli: [iris-cli]`、`telegram/discord/whatsapp/slack/signal/…: [iris-<平台>]`。
  可用单个工具集组合：`web, search, terminal, file, browser, vision, image_gen,
  skills, skills_hub, todo, tts, cronjob`。运行 `iris chat --list-toolsets` 查看。
  顶层 `toolsets` 键**已废弃**，会被忽略。
- **mcp_servers**：命名的 stdio/HTTP MCP 服务：
  ```yaml
  mcp_servers:
    filesystem:
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
      timeout: 120            # 单工具调用超时
      connect_timeout: 60     # 初始连接超时
      lazy: false             # 仅在首次调用工具时才启动
  ```

## display — CLI / 网关渲染

```yaml
display:
  compact: false                  # 单行横幅
  tool_progress: all              # off | new | all | verbose | log
  streaming: true                 # 流式输出 token 到终端
  show_reasoning: true            # 显示思考框
  interim_assistant_messages: true
  long_running_notifications: true
  busy_input_mode: interrupt      # interrupt | queue | steer
  bell_on_complete: false
  skin: default                   # default | mono | slate | daylight | …
```

## stt / tts — 语音

```yaml
stt:
  enabled: true                   # 在消息平台自动转写语音消息
  # provider: local               # local | groq | openai | mistral | deepinfra（缺省自动探测）
  language: "en"                  # 全局语言提示；"" = 自动检测
  local:
    model: "base"                 # tiny | base | small | medium | large-v3 | turbo
  openai:
    model: "whisper-1"
    timeout: 60
```

TTS 默认 Edge TTS（免费）。设 `tts.provider` 为 `gemini`、`openai`、`xai`、
`minimax`、`mistral`、`elevenlabs`、`deepinfra` 等，并配置对应 `tts.<provider>` 块。

## telemetry — 共享指标

```yaml
telemetry:
  shared_metrics:
    enabled: false                # 采集白名单内的聚合计数器
    send: false                   # 真正上传需单独开启
```

只有 `enabled` 与 `send` **同时**为 true 才会外传。每个包携带一个随机的、按 profile
隔离的 ID（不含硬件/账号/主机数据）；本地历史保留 30 天。

## 模型配置流程

1. **选 provider**：运行 `iris model`（交互式选择器），或在 `config.yaml` 里设
   `model.provider`。`auto` 按已有凭证自动探测。一方 OAuth 提供商用
   `iris auth add <provider>` 登录（如 `iris auth add nous`、`iris auth add openai-codex`）。
2. **配 API key**：
   - 内置提供商：把密钥写进 `$IRIS_HOME/.env`，如
     `OPENROUTER_API_KEY=...`、`ANTHROPIC_API_KEY=...`、`GLM_API_KEY=...`、
     `KIMI_API_KEY=...`、`MINIMAX_API_KEY=...`。
   - 自定义端点：在 `custom_providers` 里写内联 `api_key`，或用
     `key_env: VAR_NAME` 从环境变量读。
   - 命名/企业网关：在 `providers.<name>` 下用 `api_key`、`key_env` 或
     `key_cmd`（打印短期 bearer 的命令）。
3. **设 `base_url`**：主端点写在 `model.base_url`，或写在 `providers:` /
   `custom_providers` 的对应条目里。
4. **覆盖默认模型**：用 `model.default`、`--model` 参数，或会话内 `/model` 命令。
   短名可用 `model_aliases` 做别名。
5. **故障转移**：在 `fallback_providers` 列出备用路由；瞬时故障时先走主提供商、
   再走该链。辅助侧任务（视觉、网页提取、压缩、标题生成）用 `auxiliary.*` 块配置，
   默认自动探测到便宜模型。

## 环境变量

Iris 启动时加载 `$IRIS_HOME/.env`。下表列出操作者**实际会设置**的变量；
内部管道变量（会话级、启动器注入、TUI sidecar、kanban/更新机制等）不列入。

### 核心路径与 profile

| 变量 | 作用 | 默认值 | 所属组件 |
|---|---|---|---|
| `IRIS_HOME` | Iris 数据/配置目录 | `~/.iris`（Windows 为 `%LOCALAPPDATA%\iris`） | 全部 |
| `IRIS_CONFIG_PATH` / `IRIS_CONFIG` | 覆盖 `config.yaml` 路径 | `$IRIS_HOME/config.yaml` | 全部 |
| `IRIS_ENV_PATH` | 覆盖 `.env` 路径 | `$IRIS_HOME/.env` | 全部 |
| `IRIS_PROFILE` / `IRIS_PROFILE_NAME` | 激活命名 profile | 未设置（默认 profile） | 全部 |
| `IRIS_IGNORE_USER_CONFIG` | `1` = 用内置默认跑一次，忽略 `config.yaml` | 未设置 | 全部 |
| `IRIS_HOME_MODE` | 强制 `$IRIS_HOME` 的 chmod 模式（如 `0701`） | 未设置 | 全部 |
| `IRIS_UID` / `IRIS_GID` | profile 子目录的属主（Docker 用） | 未设置 | 全部 |

### 模型与运行时行为

| 变量 | 作用 | 默认值 | 所属组件 |
|---|---|---|---|
| `IRIS_MODEL` | 单次调用覆盖模型 | 未设置 | agent |
| `IRIS_INFERENCE_MODEL` / `IRIS_INFERENCE_PROVIDER` | 固定模型/提供商 | 未设置 | agent |
| `IRIS_API_KEY` | `custom` 提供商的通用 OpenAI 兼容密钥 | 未设置 | agent |
| `IRIS_BASE_URL` | `custom` 提供商的通用 OpenAI 兼容 base_url | 未设置 | agent |
| `IRIS_API_TIMEOUT` | 未配置时的请求超时（秒） | `1800` | agent |
| `IRIS_API_CALL_STALE_TIMEOUT` | 非流式卡死探测（秒） | `90` | agent |
| `IRIS_LOCAL_STREAM_STALE_TIMEOUT` | 覆盖本地端点的卡死探测 | 未设置 | agent |
| `IRIS_MAX_ITERATIONS` | 限制工具调用迭代数 | 未设置（用 `agent.max_turns`） | agent |
| `IRIS_YOLO_MODE` | `1` ≈ approvals `off` | 未设置 | agent |
| `IRIS_ACCEPT_HOOKS` | `1` = 非 TTY 运行自动接受 shell hooks | 未设置 | hooks |
| `IRIS_ROOM_LINK_URL` | 跨网关 Group Chat 的公网 HTTPS base URL | 未设置 | gateway |
| `IRIS_RESTART_AFTER_TURN_TIMEOUT` | 重启前等待进行中轮次的宽限（秒） | `1800` | gateway |
| `IRIS_RESTART_DRAIN_TIMEOUT` / `IRIS_CRON_DRAIN_TIMEOUT` | 停止/重启优雅排空（秒） | `0` / `30` | gateway |
| `IRIS_TURN_LEASE_TIMEOUT` | 别名路由等待忙会话租约（秒） | `5` | gateway |
| `IRIS_SESSION_STALL_TIMEOUT` | 会话停滞看门狗（秒，`0` = 关） | `300` | gateway |
| `IRIS_TOOL_PROGRESS` / `IRIS_TOOL_PROGRESS_MODE` | 覆盖 `display.tool_progress` | 未设置 | display |
| `IRIS_VERIFY_ON_STOP` | `1`/`0` 覆盖 `agent.verify_on_stop` | 未设置 | agent |
| `IRIS_LOCAL_STT_LANGUAGE` | STT 语言回退 | 未设置 | stt |

### Web UI（WebUI 进程）

| 变量 | 作用 | 默认值 | 所属组件 |
|---|---|---|---|
| `IRIS_WEBUI_AGENT_DIR` | Agent 源码检出目录 | 自动探测 | webui |
| `IRIS_WEBUI_PYTHON` | agent venv 的 Python 可执行文件 | 自动探测 | webui |
| `IRIS_WEBUI_HOST` | 监听地址 | `127.0.0.1` | webui |
| `IRIS_WEBUI_PORT` | 监听端口 | `8787` | webui |
| `IRIS_WEBUI_STATE_DIR` | 会话/工作区/状态目录 | `~/.iris/webui` | webui |
| `IRIS_WEBUI_DEFAULT_WORKSPACE` | 首次启动默认工作区 | `~/workspace` | webui |
| `IRIS_WEBUI_DEFAULT_MODEL` | UI 模型覆盖 | 未设置（当前 provider 默认） | webui |
| `IRIS_WEBUI_BOT_NAME` | UI 里的助手显示名 | `Iris` | webui |
| `IRIS_WEBUI_PASSWORD` | 登录密码（绑定到非回环地址时**必填**） | 未设置 | webui |
| `IRIS_WEBUI_PASSKEY` | `1` = 开启 passkey/WebAuthn 登录 | 关 | webui |
| `IRIS_WEBUI_SESSION_TTL` | 认证 cookie 有效期（秒） | `2592000`（30 天） | webui |
| `IRIS_WEBUI_SECURE` | 强制 cookie 的 `Secure` 标记 | 自动探测 | webui |
| `IRIS_WEBUI_ALLOWED_ORIGINS` | 额外允许的 CSRF 源（逗号分隔，须带 scheme） | 未设置 | webui |
| `IRIS_WEBUI_TLS_CERT` / `IRIS_WEBUI_TLS_KEY` | 直接提供 HTTPS | 未设置（明文 HTTP） | webui |
| `IRIS_WEBUI_TRUSTED_AUTH_HEADER` | 反向代理 SSO 身份头 | 未设置（关） | webui |
| `IRIS_WEBUI_TRUSTED_PROXY_CIDRS` | 受信任身份头代理的 CIDR 白名单 | 仅回环 | webui |
| `IRIS_WEBUI_ATTACHMENT_DIR` | 聊天附件存储 | `<state dir>/attachments` | webui |
| `IRIS_WEBUI_PLUGINS_DIR` | WebUI 插件目录 | `~/.iris/plugins` | webui |
| `IRIS_WEBUI_GATEWAY_API_KEY` | 轮询网关健康接口的密钥 | 未设置 | webui |
| `IRIS_PLUGINS_DEBUG` | `1` 时输出插件加载调试日志 | 未设置 | plugins |

### Dashboard / 网关 OAuth

| 变量 | 作用 | 默认值 | 所属组件 |
|---|---|---|---|
| `IRIS_DASHBOARD_OAUTH_CLIENT_ID` | Nous Portal OAuth client id | 未设置（portal 下发） | dashboard |
| `IRIS_DASHBOARD_PORTAL_URL` | Portal base URL | `https://portal.nousresearch.com` | dashboard |
| `IRIS_DASHBOARD_PUBLIC_URL` | 强制公网绝对 URL（反向代理后） | 未设置 | dashboard |
| `IRIS_DASHBOARD_OIDC_ISSUER` / `..._CLIENT_ID` / `..._SCOPES` / `..._CLIENT_SECRET` | 自建 OIDC（Authentik/Keycloak 等） | 未设置 | dashboard |

> 遥测只能由 `telemetry.shared_metrics` 配置块控制，**没有** `IRIS_TELEMETRY` 这个环境变量。

## 配置生效

修改 `config.yaml` 后**必须重启 Web UI / 网关**才能生效：

```bash
# 停止旧进程后
cd webui && python3 server.py
```

> 若提示 `agent_runtime_stale`，说明 Agent 源码或配置在运行期间被改动，重启 Web UI 即可恢复。
