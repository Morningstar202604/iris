# Quick Start

Iris 是一个**本地优先**的个人 AI 超级助手：完整的 Agent 内核 + 现代消费级 Web UI。
本指南带你 3 步跑起来。

## 1. 克隆与安装

```bash
git clone https://gitcode.com/badhope/iris.git && cd iris

# 安装 agent 核心（Hermes 内核 + 工具/插件/记忆/技能/定时任务）
cd agent && pip install -e . && cd ..
```

> 需要 Python 3.11+。建议使用 venv：
> ```bash
> python3 -m venv .venv && source .venv/bin/activate
> ```

## 2. 启动 Web UI

```bash
cd webui && python3 server.py
```

浏览器打开 **http://127.0.0.1:8787**（端口可通过 `HERMES_WEBUI_PORT` 环境变量修改）。

**关键环境变量：**

| 变量 | 作用 | 默认 |
|---|---|---|
| `HERMES_WEBUI_AGENT_DIR` | Agent 源码目录（仓库内的 `agent/`） | 自动探测 |
| `HERMES_WEBUI_STATE_DIR` | 会话/状态数据目录 | `~/.hermes` |
| `HERMES_WEBUI_PORT` | 监听端口 | `8787` |
| `HERMES_WEBUI_PASSWORD` | 访问密码（可选） | 空 = 本机免密 |

## 3. 接入模型

### 方式 A：使用内置模型
启动后进入 **设置 → 提供商**，选择一个可用模型即可。

### 方式 B：接入任意 OpenAI 兼容端点（推荐）
编辑 `~/.hermes/config.yaml`：

```yaml
model:
  provider: custom:my-provider
  default: my-model
custom_providers:
  - name: my-provider
    base_url: https://your-endpoint/v1
    api_key: your-key
    models:
      - my-model
```

保存后**重启 Web UI** 生效。

### 图像生成（可选）
Iris 的画图工具走插件机制。要把任意 OpenAI 兼容端点用作画图后端：

```yaml
plugins:
  enabled:
    - image_gen/openai
image_gen:
  provider: openai
  openai:
    provider: my-provider      # 复用上面 custom_providers 的端点与密钥
    model: my-image-model      # 端点自己的图像模型名
```

### 无人值守审批（可选）
Web UI 任务在无人值守下执行 `execute_code` 等脚本时需要审批策略：

```yaml
approvals:
  mode: smart        # smart = 安全命令自动跑，危险命令才询问
  timeout: 120
```

- `smart`：推荐，兼顾安全与自动化
- `off`：全部自动执行（仅在你完全信任脚本时使用）

## 下一步

- 阅读 [`configuration.md`](configuration.md) 了解全部配置项
- 阅读 [`usage.md`](usage.md) 了解日常功能
- 遇到问题先看 [`faq.md`](faq.md)
