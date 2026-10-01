# Deploying Iris WebUI（裸机 / VM / systemd）

> 容器化部署见 [`docker.md`](docker.md)（单容器 / 双容器 / 三容器、UID/GID 对齐、
> 权限排障均在那里）。本文覆盖**从源码 / venv 直接跑**的部署路径：进程模型、启动方式、
> 与 agent 的接法、升级步骤。
>
> 镜像 tag 现状：[CHANNEL-PENDING：双轨发布确认中，见 docker.md]——本文不写具体 tag 值。

---

## 1. 进程模型：三种形态

Iris WebUI 只有一个 Python server 进程（`server.py`），区别在于**聊天在哪执行**：

| 形态 | 聊天执行位置 | 如何开启 | 适用 |
|---|---|---|---|
| **单进程（默认，legacy）** | WebUI 进程内直接 `from run_agent import AIAgent` | 什么都不配 | 个人机、单机自托管——99% 用户 |
| **Gateway 分离** | 独立的 Iris Gateway API server（agent 侧 `gateway run`） | `IRIS_WEBUI_CHAT_BACKEND=gateway` + `IRIS_WEBUI_GATEWAY_BASE_URL` + `IRIS_WEBUI_GATEWAY_API_KEY` | 多实例共享一个 agent、多容器部署 |
| **远程 runner** | 外部 HTTP runner（`POST /v1/runs`） | `IRIS_WEBUI_RUNNER_BASE_URL`（+ `IRIS_WEBUI_RUNNER_API_KEY`） | 受控执行边界、沙箱化 runner |

> **关键事实**：默认形态下 WebUI **不连**任何外部 OpenAI 兼容 API 跑聊天；`IRIS_API_URL`
> 只用于 Tasks/cron 的健康探针，不路由聊天。想把外部模型当 provider 用，去
> Settings → Providers 加 custom provider；想把聊天整体挪到独立进程，才需要 Gateway 形态。
> 细节见 [`advanced-chat-setup.md`](advanced-chat-setup.md)。

### Gateway 是什么 / 怎么启

Gateway 是 agent 仓库侧的 HTTP API server（`command: gateway run`），对外暴露
OpenAI 兼容接口 + `/v1/runs`，用 `API_SERVER_KEY`（≥16 字符）鉴权。WebUI 侧：

```bash
export IRIS_WEBUI_CHAT_BACKEND=gateway
export IRIS_WEBUI_GATEWAY_BASE_URL=http://127.0.0.1:8642
export IRIS_WEBUI_GATEWAY_API_KEY=<与 Gateway 的 API_SERVER_KEY 完全相同>
# 可选：
# export IRIS_WEBUI_GATEWAY_USE_RUNS_API=1   # 走 /v1/runs
# export IRIS_WEBUI_GATEWAY_READ_TIMEOUT=600  # 字节静默预算，默认 600s
```

key 不匹配时 WebUI 会在探针 / 首轮聊天直接报错，并提示检查 `IRIS_WEBUI_GATEWAY_API_KEY`。

---

## 2. 启动链路（默认单进程形态）

```
./start.sh  ──►  python3 bootstrap.py --no-browser  ──►  os.execv(python, server.py)
```

`bootstrap.py` 启动时做的事（见源码 `bootstrap.py`）：

1. 加载仓库根 `.env`（`IRIS_WEBUI_PRESERVE_ENV=1` 时不覆盖已有 shell 变量）。
2. **发现 agent 目录**：`IRIS_WEBUI_AGENT_DIR` > `$IRIS_HOME/iris-agent` > 同级
   `../iris-agent` > `~/.iris/iris-agent` > `~/iris-agent` > `/usr/local/lib/iris-agent`
   > PATH 上 `iris` 启动器反推 > `IRIS_WEBUI_PYTHON` 能 import 的 `run_agent`。
   全都找不到且没有 `iris` CLI 时，自动跑官方安装脚本
   （`curl -fsSL …/agent/scripts/install.sh | bash`，`--skip-agent-install` 可禁）。
3. **选定解释器**：`IRIS_WEBUI_PYTHON` > agent venv > webui 仓库 `.venv` > `python3`。
   然后校验该解释器能否同时 import WebUI 依赖（pyyaml、cryptography）和
   `from run_agent import AIAgent`；不能时按 §3 补救。
4. 建 state 目录（`IRIS_WEBUI_STATE_DIR` 或 `$IRIS_HOME/webui`），导出
   `IRIS_WEBUI_HOST/PORT/STATE_DIR/AGENT_DIR` 给子进程。
5. 交互模式：fork detached `server.py`，轮询 `/health`，就绪后开浏览器；
   systemd/launchd/supervisord 环境（或 `--foreground` / `IRIS_WEBUI_FOREGROUND=1`）
   下直接 `os.execv` 前台托管，不做健康探针。

### 三种启动入口怎么选

| 命令 | 行为 | 停止方式 |
|---|---|---|
| `python3 bootstrap.py` | 前台跑，Ctrl-C 即停，自动开浏览器 | Ctrl-C |
| `./start.sh` | 先探针防重复启动，再 exec bootstrap（默认 `--no-browser`） | `lsof -i :8787` 找 PID kill |
| `./ctl.sh start` | 守护进程，写 `~/.iris/webui.pid`，日志 `~/.iris/webui.log` | `./ctl.sh stop` |
| `iris-webui`（pip 安装后） | 等价 `python server.py`，内部仍走 bootstrap.main() 的发现/补依赖逻辑 | 同上 |

---

## 3. 跑通 agent 的两个必备条件（实测结论）

WebUI server 进程要求它的 Python 环境里**同时**有：
- WebUI 依赖：`pyyaml>=6.0`、`cryptography>=42.0`（`webui/requirements.txt`）；
- Agent 依赖：能 `import run_agent` 且其传递依赖（openai、httpx 等）齐全。
  运行时 `api/config.py` 会把 `IRIS_WEBUI_AGENT_DIR` append 进 `sys.path`，所以
  agent 源码目录能被找到，但**依赖包必须装在解释器 site-packages 里**——
  这就是“server 起得来、一发消息报 `AIAgent not available`”的根因。

### 推荐做法 A：webui 自带 .venv + 可编辑安装 agent

```bash
cd iris
python3 -m venv webui/.venv
source webui/.venv/bin/activate
pip install -r webui/requirements.txt
pip install -e ./agent                 # 连带装好 agent 全部依赖
export IRIS_WEBUI_AGENT_DIR=$PWD/agent # 显式指向 agent 根
cd webui && ./start.sh
```

### 推荐做法 B：直接用 agent 的 venv

```bash
export IRIS_WEBUI_PYTHON=/path/to/iris-agent/venv/bin/python
# 该 venv 里补装 webui 依赖：
/path/to/iris-agent/venv/bin/python -m pip install -r webui/requirements.txt
export IRIS_WEBUI_AGENT_DIR=/path/to/iris-agent
cd webui && ./start.sh
```

> `IRIS_WEBUI_DISABLE_LOCAL_VENV=1` 适用于打包镜像：bootstrap 不会私自新建 `.venv`，
> 环境不对直接报错，逼你显式设 `IRIS_WEBUI_PYTHON`。
> 想让 server 启动时自动 pip 装 agent 依赖（目录需通过属主/权限信任检查），
> 另开 `IRIS_WEBUI_AUTO_INSTALL=1`——默认是关的。

### 手动直跑（不经 bootstrap）

```bash
cd /path/to/iris-agent        # cwd 需能让 sys.path 找到 agent
IRIS_WEBUI_PORT=8787 /path/to/agent/venv/bin/python /path/to/iris-webui/server.py
```

系统 Python 会缺 `openai`/`httpx` 等包，必须用装好依赖的解释器。

---

## 4. systemd 托管示例

```ini
# /etc/systemd/system/iris-webui.service
[Unit]
Description=Iris WebUI
After=network.target

[Service]
Type=simple
# bootstrap 检测到 INVOCATION_ID 后自动切前台 exec，无需 --foreground
Environment="IRIS_WEBUI_HOST=127.0.0.1"
Environment="IRIS_WEBUI_PORT=8787"
Environment="IRIS_WEBUI_AGENT_DIR=/opt/iris/agent"
Environment="IRIS_WEBUI_PYTHON=/opt/iris/agent/venv/bin/python"
WorkingDirectory=/opt/iris/webui
ExecStart=/opt/iris/agent/venv/bin/python /opt/iris/webui/bootstrap.py --no-browser --foreground
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

绑定公网时**必须**设 `IRIS_WEBUI_PASSWORD`（或 OIDC / 受信代理 SSO），否则 server
只允许 loopback。TLS 用 `IRIS_WEBUI_TLS_CERT` + `IRIS_WEBUI_TLS_KEY` 同时设置开启。

---

## 5. 升级路径（源码部署）

```bash
cd iris
git pull origin de-hermes          # 或你的跟踪分支
# 1) 依赖可能变动——重装两侧依赖
source webui/.venv/bin/activate    # 做法 A 的 venv；做法 B 用 agent venv
pip install -r webui/requirements.txt
pip install -e ./agent --upgrade
# 2) 迁移说明：若新版本调整了 state 布局，按 release notes 处理；
#    IRIS_WEBUI_STATE_DIR 默认跟随 IRIS_HOME，未显式设置且挪过 IRIS_HOME 的
#    老安装需要手动把旧 state 目录指过来。
./ctl.sh restart                   # 或 systemctl restart iris-webui
curl -fsS http://127.0.0.1:8787/health   # 期望 "status": "ok"
```

升级后常见错位：
- agent 与 webui 版本不匹配（`git pull` 后只重装了一侧依赖）→ 两侧都重装。
- `IRIS_WEBUI_AGENT_DIR` 指向旧 clone → 确认指向本次 pull 的目录。
- state 目录漂移 → 见 `IRIS_WEBUI_STATE_DIR` 的升级提示。

---

## 6. 容器部署（索引）

多容器 compose 文件存在于 webui 仓库根，**用途**如下，具体 tag / 端口 / 卷配置见
[`docker.md`](docker.md)：

| 文件 | 拓扑 | 用途 |
|---|---|---|
| `docker-compose.yml` | 单容器 | WebUI + agent 合一，最快上手 |
| `docker-compose.two-container.yml` | agent(gateway) + webui | agent 以 `gateway run` 独立进程跑，WebUI 经 `IRIS_WEBUI_CHAT_BACKEND=gateway` 连接——容器化版的“分离模式” |
| `docker-compose.three-container.yml` | agent + dashboard + webui | 额外独立 dashboard 服务 |

镜像 tag 现状：**[CHANNEL-PENDING：双轨发布确认中，见 docker.md]**——
发布前以 docker.md 的 Available Docker tags 段为准，本文不固化具体 tag 值。

---

## 7. 相关文档

- 全部环境变量：[`environment-variables.md`](environment-variables.md)
- Gateway 聊天 / prefill 进阶：[`advanced-chat-setup.md`](advanced-chat-setup.md)
- 远程访问（SSH 隧道 / Tailscale）：[`remote-access.md`](remote-access.md)
- 排障：[`troubleshooting.md`](troubleshooting.md)
- Windows/WSL 自启：[`wsl-autostart.md`](wsl-autostart.md)
