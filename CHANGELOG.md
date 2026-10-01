# Changelog / 更新日志

All notable changes to **Iris** (the repo-root distribution, i.e. `agent/` + `webui/`
shipped together) are documented here.
本仓库根级别的变更记录（`agent/` + `webui/` 整体发行）。

> The WebUI component keeps its own historical changelog at
> [`webui/CHANGELOG.md`](webui/CHANGELOG.md) — do not append cross-repo entries there.
> WebUI 子组件的历史变更仍维护在 `webui/CHANGELOG.md`，跨仓条目不得追加过去。
>
> Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow SemVer.

## [0.12.0] - 2026-10-01

First release under the **Iris** brand — the `de-hermes` line is cut: the former
Hermes distribution is renamed, audited, rebranded and shipped as Iris 0.12.0.
Iris 品牌首个正式版本：`de-hermes` 分支落地——原 Hermes 发行版完成全库改名、
深读审查、品牌定稿并以 Iris 0.12.0 对外发布。

### Changed

- **Hermes → Iris 全库改名完成。** 仓库、包名、CLI 入口、WebUI 标题、配置键与文档
  统一更名；`agent` 包版本号统一锁定为 `0.12.0`（`agent/pyproject.toml`）。
  Full-repo rename from Hermes to Iris: package, CLI, WebUI chrome, config keys and docs
  rebranded; agent version pinned to 0.12.0.
- **品牌定稿。** 标语 *“Calm on the surface. Capable inside.” / 表面平静，心里有数*；
  翼杖徽标资产落地 `assets/brand/`（`iris-mark.svg` / `iris-mark-256.png` /
  `iris-mark-1024.png`）；确立 4 条品牌支柱；色板规范为 accent `#4F6EF7`、
  dark `#6B8BFF`（已用于 README badges 与 landing 主按钮）。
  Brand locked: tagline, winged-staff mark under `assets/brand/`, four brand pillars,
  accent `#4F6EF7` / dark `#6B8BFF`.
- **素材清理与 mark 统一。** 原 Nous Research 相关素材完成替换/下线；landing 页与
  WebUI app mark 统一为 Iris 徽标。Nous Research assets replaced or removed; landing
  and in-app marks unified on the Iris mark.
- **双轨发布落地。** 发布策略按 [MIRROR.md](MIRROR.md) 执行：GitHub `X33834/iris`
  与 GitCode `badhope/iris` 为同等权重的 co-release 宿主；GitHub CI 在打 tag 后自动
  构建 `dist/iris-${TAG}.tar.gz|.zip` 并上传 Releases；GitCode 侧为人工/OpenAPI 上传。
  Dual-track release live: equal-weight GitHub + GitCode hosts, see MIRROR.md.
- **配置与部署文档补齐。** [`docs/configuration.md`](docs/configuration.md)（及 zh-CN
  对照）全字段补全；环境变量参考整理为 agent 侧 54 条 / WebUI 侧 109 条；裸机部署、
  quickstart、usage、faq 文档同步更新。Config reference field-complete; env-var
  inventory 54 (agent) / 109 (webui); deploy docs refreshed.

### Added

- **根级 CHANGELOG。** 本文件即新建——此前仓库根没有变更记录，全仓唯一 CHANGELOG 为
  `webui/CHANGELOG.md`（历史红线，不再跨仓追加）。Repo-root changelog established.
- **发布流程文档。** [`docs/RELEASING.md`](docs/RELEASING.md) 记录真实发版步骤（tag、
  双轨推送、CI 产物、landing 硬编码链接人工同步、registry 待落地项）。Release runbook added.
- **品牌资产目录。** `assets/brand/` 收纳徽标源文件与多尺寸 PNG，供 README、landing、
  WebUI 复用。Brand assets directory added.

### Fixed

- **全库深读审查修复 43 处问题。** 对 14 个模块、约 9 265 个文件完成逐模块深读，
  合计修复 43 处缺陷（逻辑、配置、文档与一致性问题）；另保留 84 项观察项暂不改动。
  Full-repo audit across 14 modules / ~9 265 files: 43 issues fixed, 84 observations
  deliberately retained.

### Removed

- **无用可砍文件清理。** 审查中标注为无用/冗余的文件按类别删除共 32 + 13 + 2 + 2 个，
  收缩发布面。Dead files removed across four audit buckets (32 / 13 / 2 / 2).

## [Unreleased]

No changes yet.
