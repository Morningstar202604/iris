# Releasing Iris

How to cut a tagged release. This is an **executable checklist** for the release
lead — every step has a command or a location, and the expected gate. Verified
against `.github/workflows/ci.yml`, `.github/workflows/docker-image.yml`,
`docs/index.html`, and `MIRROR.md` as of v0.12.0.

> Current version: **v0.12.0** (must match `agent/pyproject.toml`).
> Remotes follow `MIRROR.md`: `gh1` = github.com/X33834/iris (CI + Releases),
> `gitcode` = gitcode.com/badhope/iris (homepage + Releases). Mirrors `gh2` /
> `gitee` follow after the co-release homes.

---

## ① Local verification — green gate, on `de-hermes`

Run all three before committing. Each must end clean; treat the printed counts
as the gate.

```bash
# Agent tests — expect: 18 passed
cd agent && python -m pytest tests/ -q && cd ..

# WebUI suite — expect: 166 passed, 2 skipped (driven by scripts/test.sh,
# which bootstraps the webui venv; do not call pytest directly on a fresh box)
cd webui && ./scripts/test.sh tests/ -q && cd ..

# Syntax compile gate — both must print 0 errors (exit 0)
python -m compileall -q agent   -x "apps/desktop|tests|optional-skills"; echo "agent compile exit=$?"
python -m compileall -q webui   -x "_shots|docs|tests";             echo "webui compile exit=$?"
```

- [ ] Agent: `18 passed`
- [ ] WebUI: `166 passed, 2 skipped`
- [ ] compileall: both exit `0`

## ② Commit to `de-hermes`

Release lead runs (do **not** push yet — merge next):

```bash
git status                      # confirm working tree is the release state
git add -A
git commit -m "Release v0.12.0"
```

- [ ] `CHANGELOG.md` top entry = `v0.12.0`, dated today; `[Unreleased]` below empty.
- [ ] `agent/pyproject.toml` version = `0.12.0`.

## ③ Merge to `main` and push dual-track

```bash
git switch main
git merge --ff-only de-hermes      # or merge --no-ff if the lead prefers
# Co-release homes (equal weight):
git push gh1 main                 # GitHub   X33834/iris  (runs CI)
git push gitcode main             # GitCode  badhope/iris
# Mirrors:
git push gh2 main                 # GitHub  Morningstar202604/iris
git push gitee main               # Gitee   badhope/iris
```

- [ ] GitHub CI (`.github/workflows/ci.yml`) is green on the pushed `main`
      commit before tagging.

## ④ Tag `v0.12.0` and push dual-track

```bash
TAG=v0.12.0
git tag -a "$TAG" -m "Iris $TAG"
git push gh1   "$TAG"            # GitHub  — this triggers BOTH workflows below
git push gitcode "$TAG"           # GitCode
git push gh2   "$TAG"
git push gitee "$TAG"
```

- [ ] Tag exists on all four remotes.

## ⑤ GitHub CI: release assets **and** container images

Pushing the tag to GitHub triggers two workflows in
[`.github/workflows/`](../.github/workflows/):

- **`ci.yml`** (job `release`): builds
  `dist/iris-v0.12.0.tar.gz` + `dist/iris-v0.12.0.zip` and uploads them to the
  GitHub Release via `softprops/action-gh-release` (auto release notes).
- **`docker-image.yml`** (new): builds and pushes to GHCR:
  - `ghcr.io/x33834/iris-agent` (from `agent/Dockerfile`, context `agent/`)
  - `ghcr.io/x33834/iris-webui` (from `webui/Dockerfile`, context `webui/`)

  Tag semantics for `v0.12.0`: image tags `0.12.0`, `0.12`, and `latest`.

Check the run: **GitHub → Actions → the `v0.12.0` run → green**.

- [ ] `ci.yml / release` green → GitHub Release has both archives attached.
- [ ] `docker-image.yml` green for **both** matrix entries (`iris-agent`,
      `iris-webui`).
- [ ] Verify the images landed: `ghcr.io/x33834/iris-agent:latest` and
      `ghcr.io/x33834/iris-webui:latest` are pullable (first publish may need the
      package visibility set to public once in the GHCR package settings).

> Container registry is no longer PENDING: images now go through GitHub CI
> (`.github/workflows/docker-image.yml`) on tag push.

## ⑥ GitCode: manually attach release assets

GitCode CI (`.gitcode/workflows/ci.yml`, job `release`) builds the **same**
archives but **does not upload them** — it only prints instructions. Populate
the GitCode Release by hand:

1. Open https://gitcode.com/badhope/iris/releases → **New Release**.
2. Choose tag `v0.12.0`.
3. Attach both files (download the archives from the GitHub Release, or rebuild
   locally with the same tar/zip command from `ci.yml`):
   - `dist/iris-v0.12.0.tar.gz`
   - `dist/iris-v0.12.0.zip`

- [ ] GitCode Release page lists both archives (it is **not** auto-uploaded).

## ⑦ Landing page / link check

[`docs/index.html`](index.html) **hardcodes** the v0.12.0 asset URLs; it does
not track the latest tag automatically.

- If this release reuses the already-bumped generic listing links (GitCode
  buttons point at the generic `https://gitcode.com/badhope/iris/releases`
  page) — **no bump needed**, just confirm no 404.
- If GitHub / Morningstar buttons still hardcode an older `vX.Y.Z` URL, bump
  them **after** the GitHub Release exists (otherwise the download 404s), then
  push `docs/` so GitHub Pages serves it.

- [ ] `docs/index.html` download buttons resolve 200 (not 404) on GitHub and
      Morningstar links for `v0.12.0`.
- [ ] README badges still point at the version-free releases listing — no bump.

## ⑧ Release announcement

- Post the announcement: GitHub Release discussion / Discussions, and the
  mainland-China channel mirroring the GitCode release.
- Content points: new features + fixes (top of `CHANGELOG.md`), the two
  one-line install commands:
  - source archives on both homes, and
  - container: `docker pull ghcr.io/x33834/iris-agent:0.12.0` /
    `docker pull ghcr.io/x33834/iris-webui:0.12.0`.
- Note the container path is now the supported GHCR flow (step ⑤).

---

### Post-release smoke

- [ ] `CHANGELOG.md` top entry matches the tag; `[Unreleased]` empty.
- [ ] Both co-release homes (GitHub + GitCode) carry the same tag **and** both
      archives attached.
- [ ] Mirrors (`gh2`, `gitee`) received the tag.
