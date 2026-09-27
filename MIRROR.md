# 🔁 镜像与同步

Iris 以 **GitCode 为主仓**（CI、Releases、落地页），其余平台仅作可选镜像。

| 平台 | 仓库 | 定位 |
|---|---|---|
| GitCode | `badhope/iris` | ✅ 主仓（CI、Releases、Pages） |
| Gitee | `badhope/iris` | 镜像（国内加速） |
| GitHub | `X33834/iris` | 可选镜像（默认不再维护，若需海外分发再启用） |

## 方式 A — 多 remote 推送（简单，无需额外服务）

```bash
git remote -v
# gitcode https://gitcode.com/badhope/iris.git   (主)
# gitee   https://gitee.com/badhope/iris.git      (镜像)
# gh      https://github.com/X33834/iris.git      (可选镜像)

# 不要把令牌写进 remote URL —— 会留在 .git/config、shell 历史和 CI 日志里。
# 请使用凭据管理器：
#   git config --global credential.helper manager   (Windows / macOS)
#   git config --global credential.helper store     (Linux，明文文件)

# 每次提交后：
git push gitcode main && git push gitee main
# 打标签：
git tag v0.12.0 && git push gitcode v0.12.0 && git push gitee v0.12.0
```

## 方式 B — 平台原生镜像（推荐）

- **Gitee**：仓库 → 管理 → 镜像仓库管理 → 添加（来源填 GitCode `badhope/iris`）。
  Gitee 会按计划自动同步。
- **GitCode**：仓库 → 设置 → 镜像仓库（如需从 GitHub 反向同步，仅在启用 GitHub 镜像时使用）。

## 方式 C — GitCode 流水线自动同步（可选）

需要自动化时，在 `.gitcode/workflows/mirror.yml` 中添加流水线
（使用 GitCode 工作流，语法兼容 GitHub Actions，目录必须是 `.gitcode/workflows/`）。

```yaml
# .gitcode/workflows/mirror.yml
name: Mirror
on:
  push:
    branches: [main]
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Mirror to Gitee
        run: |
          git remote add gitee https://badhope:${{ secrets.GITEE_TOKEN }}@gitee.com/badhope/iris.git
          git push gitee main
```

> 将 `GITEE_TOKEN` 加入 GitCode 仓库的 设置 → 密钥/Secrets。流水线只在 CI 通过后运行，保证只有绿色提交到达镜像。

---

**原则**：在 GitCode 上开发与发布（CI + Releases），国内用户直接以 GitCode/Gitee 快速克隆。
