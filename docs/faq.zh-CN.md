# FAQ — 常见问题

[English](faq.md) · **简体中文**


## 1. 任务一直报 `HTTP 429`（限流）

**原因**：所接模型服务对免费用户有速率/总量限制。

**处理**：
- 免费配额是**滑动窗口**制——等待一段时间（分钟级）自动恢复，**不要连续重试**，重试反而延长限流。
- Iris 对 429 会自动指数退避重试 3 次，之后向用户报告限流。
- 长期使用请升级服务商的付费计划（Token Plan 等）。

## 2. 启动后提示 `agent_runtime_stale`

**原因**：Agent 源码或 `config.yaml` 在 Web UI 运行期间被修改，Web UI 无法确认更新安全完成。

**处理**：重启 Web UI（`Ctrl+C` 后重新 `python3 server.py`）。这是保护机制，不是故障。

## 3. 技能面板打不开 / `No module named 'agent'`

**原因**：Web UI 没找到 Agent 源码目录。

**处理**：用环境变量显式指定：

```bash
HERMES_WEBUI_AGENT_DIR=/path/to/iris/agent python3 server.py
```

## 4. 每次请求都很慢（数秒延迟）

**原因**：Iris 会探测模型上下文长度；对自定义端点，探测若超时会影响体验。

**处理**：
- 在 `config.yaml` 的 `model` 下显式声明 `context_length: 128000`（填你模型的实际窗口），跳过探测。
- 换用延迟更低的模型端点。

## 5. 任务执行到一半停下、没有输出

**可能原因**：`execute_code` 等脚本工具在等待审批（无人值守）。

**处理**：设置 `approvals.mode: smart`（见 [configuration.md](configuration.zh-CN.md#approvals--审批)），安全命令自动执行。

## 6. 画图工具不可用（工具列表里没有）

**原因**：未配置 `image_gen` 后端。

**处理**：在 `config.yaml` 启用 `image_gen/openai` 插件并指向你的 OpenAI 兼容端点（见 [quickstart.md](quickstart.zh-CN.md#图像生成可选)）。

## 7. 会话/历史突然只剩一部分

**处理**：Iris 在上下文接近上限时会自动压缩历史并继续任务，这是正常的内存管理。完整会话文件仍在磁盘（`~/.hermes/sessions/`）。

## 8. 如何完全卸载

```bash
# 删除状态与配置
rm -rf ~/.hermes
# 删除项目
rm -rf iris
```

## 9. 数据存在哪里？会不会上传？

- 会话、记忆、知识库、任务全部在**本机**：`~/.hermes/`。
- Iris 本身**无账号、无遥测**。只有你配置的模型服务商会收到对话请求（数据流向由你的 provider 决定）。
- 知识库检索在本地完成，不上传你的文档。

## 10. 想用别的模型（非 OpenAI 兼容）

Iris 是**协议优先**：只要端点兼容 OpenAI Chat Completions 协议（绝大多数托管服务都兼容），即可通过 `custom_providers` 接入。
