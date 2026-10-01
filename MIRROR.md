# 🔁 Mirroring & Syncing

Iris ships on a **dual-track release policy**: two hosts are *formal release
homes* (both carry the same `v*` tags and published Releases), plus two fast
mirrors for clones. This page explains how they stay in sync.

| Host | Repository | Role |
|---|---|---|
| GitHub | `X33834/iris` | ✅ **co-release primary** — CI + Releases |
| GitCode | `badhope/iris` | ✅ **co-release** — homepage + Releases (China) |
| GitHub | `Morningstar202604/iris` | mirror (release-asset mirror) |
| Gitee | `badhope/iris` | mirror (fast clones, China) |

> Both `X33834/iris` (GitHub) and `badhope/iris` (GitCode) are official,
> equal-weight release homes. CI runs on GitHub; the GitCode host is the
> homepage + Releases entry for mainland-China users. A release tag must be
> pushed to **both** co-release hosts — see the tag-push commands below.

## Option A — push to all remotes (simple, no extra service)

The release repo already carries four remotes:

```bash
git remote -v
# gitee   https://gitee.com/badhope/iris.git
# gitcode https://gitcode.com/badhope/iris.git
# gh1     https://github.com/X33834/iris.git
# gh2     https://github.com/Morningstar202604/iris.git

# Never embed tokens in remote URLs — they end up in .git/config, shell
# history, and CI logs. Use a credential helper instead:
#   git config --global credential.helper manager   (Windows / macOS)
#   git config --global credential.helper store     (Linux, plaintext file)

# After every commit:
git push gh1 main && git push gh2 main
git push gitee main && git push gitcode main

# And tags:
git tag v0.12.0 && git push gh1 v0.12.0 && git push gh2 v0.12.0
git push gitee v0.12.0 && git push gitcode v0.12.0
```

## Option B — GitHub Actions mirror (automatic, recommended)

To automate mirroring, save the following as `.github/workflows/mirror.yml`
(it is not shipped in this repo — create it in your own fork):

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
          git push gitee main  # fast-forward only; a force push hides divergence
      - name: Mirror to GitCode
        run: |
          git remote add gitcode https://badhope:${{ secrets.GITCODE_TOKEN }}@gitcode.com/badhope/iris.git
          git push gitcode main
```

> Add `GITEE_TOKEN` / `GITCODE_TOKEN` to *Settings → Secrets and variables → Actions*.
> Mirror runs after CI, so only green commits propagate to the China mirrors.

## Option C — host-native mirrors

- **Gitee**: 仓库 → 管理 → 镜像仓库管理 → 添加 (from GitHub `X33834/iris`). Gitee syncs automatically on a schedule.
- **GitCode**: 仓库 → 设置 → 镜像仓库 (from GitHub).

---

**Rule of thumb**: develop and run CI on GitHub (`X33834/iris`), cut the release
there, then push the same tag to GitCode (`badhope/iris`) so it is an equal
release home. Morningstar mirrors the release assets; Gitee serves fast clones
for users in mainland China.
