# Configuration Reference

Iris 的运行时配置位于 `~/.hermes/config.yaml`（首次启动自动创建）。
本文档覆盖公开使用最相关的配置块。全部设置项可在 Web UI **设置**页完成，配置文件的优先级最高。

## model — 主模型

```yaml
model:
  provider: custom:agnes      # 提供商 ID
  default: agnes-3.0-flash    # 默认模型
  base_url: https://your-endpoint/v1
```

- `context_length`（可选）：显式声明模型上下文窗口，避免探测延迟。
  示例：`context_length: 128000`。不设置时 Iris 自动探测（自定义端点会快速回退到默认值）。

## custom_providers — 自定义提供商

```yaml
custom_providers:
  - name: agnes                    # 提供商名（模型选择器里显示为分组名）
    base_url: https://your-endpoint/v1
    api_key: your-key
    models:
      - model-a                    # 该端点可用的模型列表
      - model-b
```

- 接入后，Web UI 的模型下拉会显示该提供商分组及其模型。
- 密钥也可以不写文件：只填 `key_env: MY_API_KEY_ENV`，从环境变量读取。

## plugins — 插件

```yaml
plugins:
  enabled:
    - web-defuddle          # 网页正文提取
    - web-knowledge-base    # 知识库搜索
    - image_gen/openai      # 画图后端（openai 兼容端点）
  disabled: []
```

插件按 `类型/名称` 引用（如 `image_gen/openai`）。`plugins.enabled` 是白名单——未列出的插件不会加载。

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

## approvals — 审批

```yaml
approvals:
  mode: smart               # manual | smart | off
  timeout: 120              # 等待人工审批的超时秒数
```

| 模式 | 行为 |
|---|---|
| `manual` | 所有脚本类工具都等人批准（**无人值守任务会超时**） |
| `smart` | 安全命令自动执行；危险命令才询问（**推荐**） |
| `off` | 全部自动执行（仅信任脚本时使用） |

Web UI / API 无人值守运行长任务时，建议 `smart`，否则 `execute_code` 等工具会等待审批直到超时。

## 提示词与个性化

- **对话人格**：Web UI **设置 → 偏好**，或 `personalities` 配置块。
- **预设提示词**：composer 上方的预设下拉，保存常用指令模板。

## 环境变量

| 变量 | 作用 |
|---|---|
| `HERMES_WEBUI_AGENT_DIR` | Agent 源码目录 |
| `HERMES_WEBUI_STATE_DIR` | 状态/会话数据目录 |
| `HERMES_WEBUI_PORT` | Web UI 端口（默认 8787） |
| `HERMES_WEBUI_PASSWORD` | 访问密码 |
| `HERMES_PLUGINS_DEBUG` | `1` 时输出插件加载调试日志 |

## 配置生效

修改 `config.yaml` 后**必须重启 Web UI**：

```bash
# 停止旧进程后
cd webui && python3 server.py
```

> 若提示 `agent_runtime_stale`，说明 Agent 源码或配置在运行期间被改动，重启 Web UI 即可恢复。
