# Iris — Brand & Product Identity

Owner-approved decisions, recorded so future work stays consistent instead of
ad-hoc. This is the single source of truth for Iris's voice, colour and mark;
`docs/UIUX-GUIDE.md` remains the source for interaction and layout mechanics.

## 1. Positioning

**Iris is a mass-market productivity assistant** (大众生产力助手) — not a
developer workbench.

What that means in practice:

| | Implication |
|---|---|
| Information density | Prefer fewer, clearer controls on screen. Progressive disclosure over showing every switch at once. |
| Vocabulary | Plain language. Avoid internal jargon (`btw`, `bg_task_complete`, "ticker", "sidecar") in anything a user reads. |
| Empty states | Every empty state must offer the action that fills it. A selection-only empty state ("select a memory section") gets **no** fake button. |
| Guidance | Lead with what the user can do, not with system status. |
| Terminology of record | `profile` = 配置, `workspace` = 工作区, `session` = 会话, `skill` = 技能, `memory` = 记忆, `log` = 日志. |

## 2. Name

**Iris** is the product name and is final. The goddess of the rainbow is the
conceptual source: the product spans many capabilities under one calm surface.

The upstream codebase still uses `Iris` in **internal identifiers only** —
`iris-*` localStorage keys, `/api/...` paths, CSS class names, the `iris`
CLI entry point. These MUST be preserved: they are protocol and stored-state
compatibility, and renaming them would silently drop users' saved preferences.

**Rule: no user-visible string may contain "Iris".** Clarified 2026-09-30:
the rule governs **functional chrome** — toast, buttons, empty-state copy,
loading strings — where an incidental product name or internal codename would
be noise. It does **not** forbid brand moments (wordmark lockups, taglines,
banners, landing pages, the README header), where saying "Iris" is the point.
Note: the test named below verifies i18n bundle integrity only; it does not
grep for the literal "Iris".

## 3. Colour

One readable accent for all functional chrome, plus a spectrum reserved for
brand moments.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--accent` | `#4F6EF7` | `#6B8BFF` | primary buttons, active nav, focus, links |
| `--brand-indigo` | `#4F6EF7` | `#6B8BFF` | brand alias of the accent |
| `--brand-violet` | `#8B5CF6` | — | spectrum only |
| `--brand-magenta` | `#EC4899` | — | spectrum only |
| `--brand-amber` | `#F59E0B` | — | spectrum only |
| `--brand-spectrum` | `linear-gradient(135deg,#6366F1,#8B5CF6 35%,#EC4899 70%,#F59E0B)` | same | logo, empty-state accent, marketing surfaces |
| `--brand-spectrum-soft` | same hues at 10–14% alpha | — | decorative backgrounds behind empty states |

**Cascade note.** The default theme's accent is set by the *later* `:root` /
`:root.dark` blocks in `static/style.css` (around the 7335/7358 region), not by
the first `:root`. The first `:root` is a warm fallback that is currently
overridden; it was also carrying the last of the old gold palette
(`#B8860B` light / `#FFD700` dark) and has been moved to the indigo family so
removing the override later cannot resurrect the old brand. When you change the
brand accent, change the **effective** block and verify with a rendered
`getComputedStyle(document.documentElement).getPropertyValue('--accent')` — the
first `:root` will lie to you.

Rules:

1. The **spectrum is never used for text, borders, or body copy** — a
   multi-hue gradient on a label destroys legibility. It is a surface treatment.
2. Contrast: `--accent` measures about 5.5:1 on the light `--bg` and about 7:1
   on the dark `--bg`, so normal text on an accent-filled button passes WCAG AA.
3. The 21 skins keep their **own** accent on purpose — a skin that borrowed the
   brand indigo would stop being a skin. They must not read `--brand-*`.
4. The default theme's accent used to be Iris gold (`#B8860B` / `#FFD700`).
   That was the last place the old brand showed through in the default theme.

## 4. Mark

The existing winged-staff mark is kept; only its **finish** was refined
(owner decision). Changes made:

- The halo behind the empty-state mark shrank from a 190px disc to 132px and
  dropped to ~10% alpha, because the previous glow read as dated.
- Replaced with a spectrum-tinted radial (`--logo-glow`) so the glow is on-brand
  instead of a leftover blue/cyan.
- Added a low drop shadow so the mark holds on both light and dark surfaces.

Rules: the mark is never recoloured per-skin, never animated, and never
replaced with an emoji or a product glyph inside body copy.

**Mark assets (owner-approved 2026-09-30).** Exported from the app favicon
(`webui/static/favicon.svg`, the winged-staff), transparent background,
brand-indigo gradient `#4F6EF7 → #6B8BFF`:

- `assets/brand/iris-mark.svg` — master vector
- `assets/brand/iris-mark-1024.png` — primary (transparent 1024×1024)
- `assets/brand/iris-mark-256.png` — small icon (transparent 256×256)

Desktop / installer / intro-reveal brand tiles and the landing page load these
assets. The landing page and the app favicon now share one mark source.

## 5. Typography & spacing

Already tokenised in `static/style.css` under `:root` — do not add raw values:

- `--font-ui` — system UI stack
- `--font-size-xs/sm/md` = 11/12/14px
- `--space-1..4` = 4/8/12/16px
- `--radius-sm/md/card/lg/pill` = 4/8/8/12/999px

## 6. Voice

- Lead with the outcome, not the mechanism. "New scheduled job", not
  "Create a cron entry".
- Errors say what to do next. The scheduled-jobs hint names the real command
  (`iris gateway`) because that is the command that exists.
- Never blame the user. No exclamation marks in system messages.

## 7. Localisation as a brand requirement

Chinese and English are both first-class. Every user-visible string goes through
`t()` / `data-i18n`; a hardcoded literal in either direction is a defect, not a
style choice. A literal that is deliberately untranslated (skill and plugin
manifest text, provider and model catalogues, skin brand names, paths, versions)
must be listed or marked — content is not chrome.

Verification: `tests/test_issue_ui_chrome_i18n.py` (static invariants) plus a
per-screen walk of 18 screens × 2 locales asserting every `[data-i18n*]` element
resolves to a non-empty value that is not the raw key.

## 8. Tagline & wordmark lockup

**Owner-approved 2026-09-30.** The primary tagline is final; secondary
candidates below remain available for context-specific surfaces (privacy pages,
channel onboarding, etc.) but the lockup is:

- **Primary (approved):** `Calm on the surface. Capable inside.`
- **中文（定稿）:** `表面平静，心里有数`（同意变体：`表面平静，内在全能`；主常量以
  `表面平静，心里有数` 为准）
- **Sub-line:** `A local-first productivity assistant` / `一个本地优先的生产力助手`

Usage: tagline appears in brand moments only (README header, landing hero,
CLI/TUI banner, onboarding). It never repeats inside functional copy. All
touchpoints carry the approved line; swaps are single-constant edits per
surface.

Secondary candidates (approved for style; reserved for specific contexts):

| # | EN | 中文 | Angle |
|---|---|---|---|
| 2 | Your work stays on your device. | 你的数据，留在你手里 | local-first ownership (privacy/download pages) |
| 3 | Use it wherever you already talk. | 你在哪儿聊，它就在哪儿 | open gateway / multi-channel |
| 4 | It handles the work. You decide. | 它来做事，你拿主意 | outcome-first, human-in-command |
| 5 | Get things done, quietly. | 安静地，把事做完 | calm capability, generic-safe |

## 9. Brand pillars

1. **Calm Capability — 平静的力量.** A quiet, uncluttered surface over
   genuinely wide capability. Default screens stay low-density; new features use
   progressive disclosure; the mark is never recoloured, animated, or replaced
   with an emoji; system messages carry no exclamation marks.
2. **Local-First & Ownership — 本地优先，数据归你.** User data and config
   live on the user's device by default (`~/.iris`), not in a vendor cloud.
   Anything that leaves the device is explicit opt-in; backup, migration and
   troubleshooting all work from local files; leaving is always a real option.
3. **Open & Portable — 开放，可带走.** Open message formats (gateway /
   JSON-RPC), a documented plugin ecosystem, config that migrates losslessly.
   Interop with where people already talk (Telegram, Discord, WeChat, self-hosted)
   is a feature; lock-in is not a business model.
4. **Outcome-First — 只讲结果.** Say what was done, not the mechanism behind it.
   Errors give the next step and never blame the user; if a feature needs jargon
   to explain, the design is not done yet.

## 10. Known follow-ups

- Density reduction for the mass-market positioning has not been done yet: the
  composer still exposes profile / workspace / model / reasoning / toolsets in one
  row. Their visual weight was reduced; consolidating them behind one "settings"
  affordance is the next step.
- **Tagline:** approved (see §8) — no follow-up.
- The other 12 locales intentionally fall back to English rather than shipping
  machine translation. Decide per-locale before adding new copy to them.
- **Mark assets:** exported to `assets/brand/` (see §4); desktop/installer/
  intro-reveal re-pointed to the winged-staff mark. Nous mascot image files
  (`nous-girl.jpg`, `nous-badge.png`, `intro-nous-girl.png`) remain on disk as
  upstream assets; any remaining visual uses are listed as candidates until
  replaced.
- **Landing mark:** unify the landing page with the winged-staff mark from
  `assets/brand/` (in progress 2026-09-30).

## 11. Brand audit corrections (2026-09-30)

- CLI/TUI banners: removed "Nous Research · Messenger of the Digital Gods"
  (Hermes mythology residue) and the unconditional "· Nous Research" suffix on
  model rows — Iris is a community fork, not a Nous product.
- CLI ASCII banner recoloured from the retired gold palette to the indigo ramp
  (BRAND.md §3.4).
- `webui/static/style.css` first `:root.dark` migrated from gold to the indigo
  family; stale "already use gold accent" comment fixed.
- Landing page ZH copy no longer self-references ("rebuild of Iris"); attribution
  now matches EN ("community fork of Hermes, originally by Nous Research").
- Non-EN READMEs (zh/es/ur) lede and H1 corrected to the fork attribution and
  the Iris name.
- `onboarding.js` hardcoded mixed-language literal split into `t()` keys.

## 12. Owner decisions (2026-09-30, tagline & mark)

- **Tagline final:** #1 "Calm on the surface. Capable inside." /
  `表面平静，心里有数` approved as the primary lockup (see §8).
- **Mark assets:** exported the winged-staff from the app favicon to
  `assets/brand/` (SVG + 1024/256 transparent PNG, brand-indigo gradient); all
  brand tiles re-pointed to these assets.
- **Mark unification:** the landing page inline mark is replaced with the
  winged-staff; the landing/app mark sources are now one.
- **Nous asset policy:** replace where a static winged-staff works (installer
  tile, onboarding badge, intro scene); keep the Nous-sourced animation textures
  only where a static mark would break the scene, tracked as candidates.
