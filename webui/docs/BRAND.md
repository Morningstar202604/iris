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

The upstream codebase still uses `Hermes` in **internal identifiers only** —
`hermes-*` localStorage keys, `/api/...` paths, CSS class names, the `hermes`
CLI entry point. These MUST be preserved: they are protocol and stored-state
compatibility, and renaming them would silently drop users' saved preferences.

**Rule: no user-visible string may contain "Hermes".** Verified by
`tests/test_issue_ui_chrome_i18n.py` and the per-screen zh/en acceptance walk.

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
4. The default theme's accent used to be Hermes gold (`#B8860B` / `#FFD700`).
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
  (`hermes gateway`) because that is the command that exists.
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

## 8. Known follow-ups

- Density reduction for the mass-market positioning has not been done yet: the
  composer still exposes profile / workspace / model / reasoning / toolsets in one
  row. Their visual weight was reduced; consolidating them behind one "settings"
  affordance is the next step.
- No tagline / wordmark lockup yet.
- The other 12 locales intentionally fall back to English rather than shipping
  machine translation. Decide per-locale before adding new copy to them.
