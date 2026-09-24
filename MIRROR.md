# 🔁 Mirroring & Syncing

Iris is published on four code hosts. This page explains how the mirrors stay in sync.

| Host | Repository | Primary? |
|---|---|---|
| GitHub | `X33834/iris` | ✅ primary (CI, Releases) |
| GitHub | `Morningstar202604/iris` | mirror |
| Gitee | `badhope/iris` | mirror (fast in China) |
| GitCode | `badhope/iris` | mirror (fast in China) |

## Option A — push to all remotes (simple, no extra service)

The release repo already carries four remotes:

```bash
git remote -v
# gitee   https://badhope:<TOKEN>@gitee.com/badhope/iris.git
# gitcode https://badhope:<TOKEN>@gitcode.com/badhope/iris.git
# gh1     https://x33834:<TOKEN>@github.com/X33834/iris.git
# gh2     https://Morningstar202604:<TOKEN>@github.com/Morningstar202604/iris.git

# After every commit:
git push gh1 main && git push gh2 main
git push gitee main && git push gitcode main

# And tags:
git tag v0.12.0 && git push gh1 v0.12.0 && git push gh2 v0.12.0
git push gitee v0.12.0 && git push gitcode v0.12.0
```

## Option B — GitHub Actions mirror (automatic, recommended)

Add a workflow that mirrors every push to the China hosts (see `.github/workflows/mirror.yml`):

```yaml
# .github/workflows/mirror.yml
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
          git push -f gitee main
      - name: Mirror to GitCode
        run: |
          git remote add gitcode https://badhope:${{ secrets.GITECODE_TOKEN }}@gitcode.com/badhope/iris.git
          git push -f gitcode main
```

> Add `GITEE_TOKEN` / `GITECODE_TOKEN` to *Settings → Secrets and variables → Actions*.
> Mirror runs after CI, so only green commits propagate to the China mirrors.

## Option C — host-native mirrors

- **Gitee**: 仓库 → 管理 → 镜像仓库管理 → 添加 (from GitHub `X33834/iris`). Gitee syncs automatically on a schedule.
- **GitCode**: 仓库 → 设置 → 镜像仓库 (from GitHub).

---

**Rule of thumb**: develop on GitHub (CI + Releases), and let the China hosts serve
fast clones for users in mainland China.
