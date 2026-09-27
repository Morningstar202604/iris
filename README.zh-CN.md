# ✦ Iris — 你的个人 AI 超级助手

> **快 · 轻 · 完全属于你。**
> 开源 **Hermes** 智能体框架的 Iris 发行版——全新重写的消费级 Web UI，叠加精简的本地优先内核。
> 100% 协议驱动、不绑定厂商、不臃肿。只有你，和你的 AI。

[English](README.md) · **简体中文**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)
![Plugins](https://img.shields.io/badge/plugins-275%2B-6B8BFF.svg)
![i18n](https://img.shields.io/badge/i18n-14%20languages-green.svg)
[![官方仓库](https://img.shields.io/badge/✦%20Iris-gitcode.com%2Fbadhope%2Firis-4F6EF7)](https://gitcode.com/badhope/iris)
[![下载](https://img.shields.io/badge/⬇%20%E4%B8%8B%E8%BD%BD-v0.12.0-12B76A)](https://gitcode.com/badhope/iris/releases)

---

## 🌐 官方仓库 · 先睹为快

**→ [gitcode.com/badhope/iris](https://gitcode.com/badhope/iris)** — GitCode 官方主页：源码、发布、Issue，以及仓库内落地页（`docs/`）。

| 下载 | 格式 | 大小 | 适用 |
|---|---|---|---|
| [⬇ iris-v0.12.0.zip](https://gitcode.com/badhope/iris/releases) | ZIP | 72 MB | **Windows / macOS — 推荐** |
| [⬇ iris-v0.12.0.tar.gz](https://gitcode.com/badhope/iris/releases) | TAR.GZ | 67 MB | Linux / 服务器 — 完整源码树 |

---

## 🚀 快速开始 — 三步上手

```bash
# 1. 克隆
git clone https://gitcode.com/badhope/iris.git && cd iris

# 2. 安装 agent 核心
cd agent && pip install -e . && cd ..

# 3. 启动 Web UI
cd webui && python3 server.py
# → 浏览器打开 http://127.0.0.1:8787
```

**搞定。** 选择内置模型，或接入*任意* OpenAI 兼容端点：

```yaml
model:
  provider: custom:my-provider
  default: my-model
custom_providers:
  - name: my-provider
    base_url: https://your-endpoint/v1
    api_key: your-key
```

---

## ⚡ 为什么选 Iris？（对比原版 Hermes）

Hermes 是杰出的智能体框架——但它越来越重。**Iris** 保留完整的 Hermes 核心，同时让整体体验向现代消费级 AI 应用看齐：

| | Hermes（原版） | **Iris** |
|---|---|---|
| ⚡ 启动速度 | 慢，全量加载 | **秒级 — 懒加载 + uvloop** |
| 📦 体积 | 臃肿 | **更精简 — Web UI 仅需 pyyaml + cryptography 两个依赖** |
| 🖥️ Web UI | 开发工具风格 | **现代消费级界面** — 亮/暗主题、9 款皮肤、命令面板 |
| 🔌 模型支持 | 逐厂商适配器 | **协议优先** — 任意 OpenAI 兼容端点即插即用 |
| 🧩 插件 | 全部内置 | **275+ 目录，按需安装/卸载** |
| 📚 知识库 | 无 | **RAG + 中文精准全文检索** |
| 🔒 隐私 | — | **本地优先。无账号。无遥测。** |

---

## 🏗️ 架构 — 简洁设计

```mermaid
flowchart LR
    U["🌐 Web UI<br/>聊天 · 设置 · 插件<br/>命令面板"] --> S["🐍 Python 服务端<br/>api/routes.py · 流式"]
    S --> A["⚙️ Hermes Agent 核心<br/>工具 · 记忆 · 技能 · 定时"]
    S --> KB[("📚 知识库<br/>SQLite FTS5 · 中文检索")]
    S --> PM["🧩 插件管理器<br/>275+ 目录 · 按需加载"]
    S --> PL["🤖 协议层<br/>OpenAI 兼容"]
    PL --> M["任意 LLM 端点<br/>一个 base_url + key"]
    A --> T1["🛠️ 工具<br/>网页 · 终端 · 文件"]
    A --> T2["🧠 记忆与技能<br/>长期记忆 · 定时任务"]
```

**两个组件，一套无缝体验：**
- `agent/` — 重构后的 Hermes 核心：工具、插件、记忆、技能、定时、协议路由
- `webui/` — 现代控制界面：聊天、设置、插件市场、知识库

---

## ✨ 你能得到什么

| | |
|---|---|
| ⚡ **轻量内核** | uvloop 事件循环、模块懒加载、精简运行时 |
| 🔌 **任意模型任意厂商** | OpenAI 兼容协议层 — 填 base_url + key 即用 |
| 🧩 **插件生态** | **275+ 插件**，一键安装 / 卸载 / 启停 |
| 📚 **知识库 RAG** | 上传文档 → 本地中文索引 → 基于*你的数据*作答 |
| 🎨 **现代 Web UI** | 命令面板（`Ctrl+Shift+P`）、9 款皮肤、520+ 设置项 |
| 🧠 **记忆与技能** | 长期记忆、技能中心、定时任务、看板、待办、会话搜索 |
| 🗣️ **语音就绪** | 语音输入 + 免提语音模式 + 语音合成 |
| 🌐 **14 种语言** | 完整国际化，默认中文，随时切换 |
| 🔒 **本地优先 · 私密** | 会话、记忆、知识全部留在*你的机器* |

---

## 🖥️ 界面截图

截图与架构说明见仓库落地页：[gitcode.com/badhope/iris](https://gitcode.com/badhope/iris)（仓库内 `docs/`）。

---

## 🔄 与 Hermes 的关系

Iris 是 **[Hermes](https://github.com/NousResearch/hermes-agent)**（Nous Research 的开源智能体框架）的
**独立深度定制发行版**。我们：

- **保留完整的 Hermes 核心** — 沿用上游模块布局，上游修复可干净合并
- **重写整个前端** — 主流消费应用风格
- **精简部署面** — Web UI 仅两个 Python 依赖，重型厂商依赖全部可选
- **新增**知识库 RAG、命令面板、预设提示词、ECharts 图表渲染等

---

## 📄 许可与致谢

采用 **MIT License**，基于 **[Hermes](https://github.com/NousResearch/hermes-agent)**（**Nous Research**，MIT）构建。
保留原始版权与署名。完整协议见 [`LICENSE`](LICENSE)。

---

## 💬 参与贡献

- ⭐ 觉得 Iris 有用就 **Star** 一下
- 🐛 **提 Issue** — 我们快速修复
- 🧩 向插件目录 **发布插件**
- 🌍 帮助 Iris **翻译**成更多语言

**Iris — 你的 AI，你的规则。**
