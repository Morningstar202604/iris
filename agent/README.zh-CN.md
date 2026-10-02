<p align="center">
  <img src="assets/banner.png" alt="Iris Agent" width="100%">
</p>

# Iris Agent ✦

<p align="center">
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/X33834/iris/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-lightgrey?style=for-the-badge" alt="English"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
</p>

**Iris——你的个人 AI 助手的代理核心**，是 [Nous Research](https://nousresearch.com) 开源智能体框架 Hermes 的社区 fork（fork 时上游 0.21.4；完全自包含，运行时不依赖上游包）。它是唯一内置学习闭环的智能代理——从经验中创建技能，在使用中改进技能，主动持久化知识，搜索过往对话，并在跨会话中逐步构建对你的深度理解。可以在 $5 的 VPS 上运行，也可以在 GPU 集群上运行，或者使用几乎零成本的 Serverless 基础设施。它不绑定你的笔记本——你可以在 Telegram 上与它对话，而它在云端 VM 上工作。

支持任意模型——[Nous Portal](https://portal.nousresearch.com)、[OpenRouter](https://openrouter.ai)（200+ 模型）、[NVIDIA NIM](https://build.nvidia.com)（Nemotron）、[小米 MiMo](https://platform.xiaomimimo.com)、[z.ai/GLM](https://z.ai)、[Kimi/Moonshot](https://platform.moonshot.ai)、[MiniMax](https://www.minimax.io)、[Hugging Face](https://huggingface.co)、OpenAI，或自定义端点。使用 `iris model` 即可切换——无需改代码，无锁定。

<table>
<tr><td><b>真正的终端界面</b></td><td>完整的 TUI，支持多行编辑、斜杠命令自动补全、对话历史、中断重定向和流式工具输出。</td></tr>
<tr><td><b>随你所在</b></td><td>Telegram、Discord、Slack、WhatsApp、Signal 和 CLI——全部从单个网关进程运行。语音备忘录转写、跨平台对话连续性。</td></tr>
<tr><td><b>闭环学习</b></td><td>代理管理记忆并定期自我提醒。复杂任务后自动创建技能。技能在使用中自我改进。FTS5 会话搜索配合 LLM 摘要实现跨会话回溯。<a href="https://github.com/plastic-labs/honcho">Honcho</a> 辩证式用户建模。兼容 <a href="https://agentskills.io">agentskills.io</a> 开放标准。</td></tr>
<tr><td><b>定时自动化</b></td><td>内置 cron 调度器，支持向任何平台投递。日报、夜间备份、周审计——全部用自然语言描述，无人值守运行。</td></tr>
<tr><td><b>委派与并行</b></td><td>生成隔离子代理处理并行工作流。编写 Python 脚本通过 RPC 调用工具，将多步管道压缩为零上下文开销的轮次。</td></tr>
<tr><td><b>随处运行</b></td><td>六种终端后端——本地、Docker、SSH、Daytona、Singularity 和 Modal。Daytona 和 Modal 提供 Serverless 持久化——代理环境空闲时休眠、按需唤醒，空闲期间几乎零成本。$5 VPS 或 GPU 集群都能跑。</td></tr>
<tr><td><b>研究就绪</b></td><td>批量轨迹生成、轨迹压缩——用于训练下一代工具调用模型。</td></tr>
</table>

---

## 快速安装

```bash
git clone https://gitcode.com/badhope/iris.git && cd iris/agent && ./setup-iris.sh
```

支持 Linux、macOS、WSL2 和 Android (Termux)。安装程序会自动处理平台特定的配置。

> **Android / Termux：** 已测试的手动安装路径请参考 [Termux 指南](../docs/quickstart.md)。在 Termux 上，Iris 会安装精选的 `.[termux]` 扩展，因为完整的 `.[all]` 扩展会拉取 Android 不兼容的语音依赖。
>
> **Windows：** 在 PowerShell 中运行：
> ```powershell
> git clone https://gitcode.com/badhope/iris.git; Set-Location iris\agent; .\setup-iris.sh
> ```
> 安装完成后，可能需要重启终端，然后运行 `iris` 开始对话。

安装后：

```bash
source ~/.bashrc    # 重新加载 shell（或: source ~/.zshrc）
iris              # 开始对话！
```

---

## 快速入门

```bash
iris              # 交互式 CLI — 开始对话
iris model        # 选择 LLM 提供商和模型
iris tools        # 配置启用的工具
iris config set   # 设置单个配置项
iris gateway      # 启动消息网关（Telegram、Discord 等）
iris setup        # 运行完整设置向导（一次性配置所有内容）
iris claw migrate # 从 OpenClaw 迁移（如果来自 OpenClaw）
iris update       # 更新到最新版本
iris doctor       # 诊断问题
```

📖 **[完整文档 →](https://gitcode.com/badhope/iris/tree/main/docs)**

---

## 省去到处收集 API Key — Nous Portal

Iris 始终允许你使用任意服务商，这点不会改变。但如果你不想为模型、网页搜索、图像生成、TTS、云浏览器分别去申请五个不同的 API Key，**[Nous Portal](https://portal.nousresearch.com)** 用一个订阅就能覆盖全部：

- **300+ 模型** — 用 `/model <name>` 随时切换
- **Tool Gateway** — 网页搜索（Firecrawl）、图像生成（FAL）、文本转语音（OpenAI）、云浏览器（Browser Use），全部通过订阅托管。无需额外注册任何账户。

全新安装时一条命令即可：

```bash
iris setup --portal
```

它会通过 OAuth 登录、把 Nous 设为推理服务商，并启用 Tool Gateway。随时用 `iris portal info` 查看路由状态。完整说明见 [Tool Gateway 文档](../docs/usage.md)。

你随时可以按工具单独切回自己的 API Key — Gateway 是按工具粒度生效的，不是一刀切。

---

## CLI 与消息平台 快速对照

Iris 有两种入口：用 `iris` 启动终端 UI，或运行网关从 Telegram、Discord、Slack、WhatsApp、Signal 或 Email 与之对话。进入对话后，许多斜杠命令在两种界面中通用。

| 操作 | CLI | 消息平台 |
|------|-----|----------|
| 开始对话 | `iris` | 运行 `iris gateway setup` + `iris gateway start`，然后给机器人发消息 |
| 开始新对话 | `/new` 或 `/reset` | `/new` 或 `/reset` |
| 更换模型 | `/model [provider:model]` | `/model [provider:model]` |
| 设置人格 | `/personality [name]` | `/personality [name]` |
| 重试或撤销上一轮 | `/retry`、`/undo` | `/retry`、`/undo` |
| 压缩上下文 / 查看用量 | `/compress`、`/usage`、`/insights [--days N]` | `/compress`、`/usage`、`/insights [days]` |
| 浏览技能 | `/skills` 或 `/<skill-name>` | `/skills` 或 `/<skill-name>` |
| 中断当前工作 | `Ctrl+C` 或发送新消息 | `/stop` 或发送新消息 |
| 平台特定状态 | `/platforms` | `/status`、`/sethome` |

完整命令列表请参阅 [CLI 指南](../docs/usage.md) 和 [消息网关指南](../docs/usage.md)。

---

## 文档

所有文档位于 **[docs/](../docs/)**：

| 章节 | 内容 |
|------|------|
| [快速开始](../docs/quickstart.md) | 安装 → 设置 → 2 分钟内开始首次对话 |
| [CLI 使用](../docs/usage.md) | 命令、快捷键、人格、会话 |
| [配置](../docs/configuration.md) | 配置文件、提供商、模型、所有选项 |
| [消息网关](../docs/usage.md) | Telegram、Discord、Slack、WhatsApp、Signal、Home Assistant |
| [安全](../docs/usage.md) | 命令审批、DM 配对、容器隔离 |
| [工具与工具集](../docs/usage.md) | 40+ 工具、工具集系统、终端后端 |
| [技能系统](../docs/usage.md) | 过程记忆、技能中心、创建技能 |
| [记忆](https://gitcode.com/badhope/iris/tree/main/docs) | 持久记忆、用户画像、最佳实践 |
| [MCP 集成](https://gitcode.com/badhope/iris/tree/main/docs) | 连接任意 MCP 服务器扩展能力 |
| [定时调度](https://gitcode.com/badhope/iris/tree/main/docs) | 定时任务与平台投递 |
| [上下文文件](https://gitcode.com/badhope/iris/tree/main/docs) | 影响每次对话的项目上下文 |
| [架构](https://gitcode.com/badhope/iris/tree/main/docs) | 项目结构、代理循环、关键类 |
| [贡献](https://gitcode.com/badhope/iris/tree/main/docs) | 开发设置、PR 流程、代码风格 |
| [CLI 参考](https://gitcode.com/badhope/iris/tree/main/docs) | 所有命令和标志 |
| [环境变量](https://gitcode.com/badhope/iris/tree/main/docs) | 完整环境变量参考 |

---

## 从 OpenClaw 迁移

如果你来自 OpenClaw，Iris 可以自动导入你的设置、记忆、技能和 API 密钥。

**首次安装时：** 安装向导（`iris setup`）会自动检测 `~/.openclaw` 并在配置开始前提供迁移选项。

**安装后任意时间：**

```bash
iris claw migrate              # 交互式迁移（完整预设）
iris claw migrate --dry-run    # 预览将要迁移的内容
iris claw migrate --preset user-data   # 仅迁移用户数据，不含密钥
iris claw migrate --overwrite  # 覆盖已有冲突
```

导入内容：
- **SOUL.md** — 人格文件
- **记忆** — MEMORY.md 和 USER.md 条目
- **技能** — 用户创建的技能 → `~/.iris/skills/openclaw-imports/`
- **命令白名单** — 审批模式
- **消息设置** — 平台配置、允许用户、工作目录
- **API 密钥** — 白名单中的密钥（Telegram、OpenRouter、OpenAI、Anthropic、ElevenLabs）
- **TTS 资产** — 工作区音频文件
- **工作区指令** — AGENTS.md（使用 `--workspace-target`）

使用 `iris claw migrate --help` 查看所有选项，或使用 `openclaw-migration` 技能进行交互式代理引导迁移（含干运行预览）。

---

## 贡献

欢迎贡献！请参阅 [贡献指南](https://gitcode.com/badhope/iris/tree/main/docs) 了解开发设置、代码风格和 PR 流程。

贡献者快速开始——使用标准安装器，然后在它创建的完整 git checkout 中开发：
`$IRIS_HOME/iris-agent`（通常是 `~/.iris/iris-agent`）。这会匹配
`iris update`、托管 venv、lazy dependencies、gateway 和 docs tooling 使用的布局。

```bash
git clone https://gitcode.com/badhope/iris.git && cd iris/agent && ./setup-iris.sh
cd "${IRIS_HOME:-$HOME/.iris}/iris-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

手动克隆备用路径（用于一次性 clone / CI，或你明确不想使用 managed install layout 时）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
python -m pytest tests/ -q
```

---

## 社区

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [技能中心](https://agentskills.io)
- 🐛 [问题反馈](https://gitcode.com/badhope/iris/issues)
- 💡 [讨论区](https://github.com/X33834/iris/discussions)
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — 社区微信桥接：在同一微信账号上运行 Iris Agent 和 OpenClaw。

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

上游框架 Hermes 由 [Nous Research](https://nousresearch.com) 构建；Iris 是其社区 fork。
