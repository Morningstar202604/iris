"""Regression: the Iris brand layer.

Two things this locks down, both of which were real defects:

1. The default theme's ``--accent`` comes from the *later* ``:root`` /
   ``:root.dark`` blocks, not the first ``:root``. Changing only the first one
   is silently dead code, and the first ``:root`` used to carry the last of the
   old gold palette. Assert no gold survives and that the brand tokens match the
   values the cascade actually resolves.
2. Every empty state that has a creation path must offer a primary CTA wired to
   a function that really exists — a CTA that navigates to the panel you are
   already on is worse than no CTA, because it looks actionable.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
CSS = (STATIC / "style.css").read_text(encoding="utf-8")
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
BUNDLE = "\n".join(p.read_text(encoding="utf-8") for p in sorted(STATIC.glob("*.js")))

# The old brand's gold, in the base palette and in the dark palette.
OLD_GOLD = ["#B8860B", "#FFD700", "#996F08", "#8B6508", "#FFBF00"]


def test_no_old_gold_palette_survives():
    """The last visible trace of the previous brand was the warm gold accent."""
    for token in OLD_GOLD:
        assert f"--accent:{token}" not in CSS, (
            f"--accent is still {token}; the effective default-theme blocks must "
            "carry the Iris indigo, not the old gold"
        )


def test_brand_tokens_declare_the_spectrum():
    for token in ("--brand-indigo:", "--brand-violet:", "--brand-magenta:",
                  "--brand-amber:", "--brand-spectrum:", "--brand-spectrum-soft:"):
        assert token in CSS, f"brand token {token} is not defined"


def test_effective_accent_blocks_define_the_brand_indigo():
    """The last :root / :root.dark block wins the cascade — assert it is branded."""
    # Capture the selector too — the body alone cannot tell :root from :root.dark.
    blocks = re.findall(r"(:root(?:\.dark)?[^{]*)\{([^}]*)\}", CSS, re.S)
    assert blocks, "no :root blocks found"
    effective_light, effective_dark = None, None
    for selector, block in blocks:
        m = re.search(r"--accent:\s*(#[0-9A-Fa-f]{6})", block)
        if not m:
            continue
        if selector.strip().startswith(":root.dark"):
            effective_dark = m.group(1)
        elif effective_light is None or selector.strip() == ":root":
            effective_light = m.group(1)
    # The LAST plain-:root and LAST :root.dark definitions win the cascade.
    plain = [(s, b) for s, b in blocks if s.strip() == ":root"]
    dark = [(s, b) for s, b in blocks if s.strip() == ":root.dark"]
    for label, group, key in (("light", plain, "light"), ("dark", dark, "dark")):
        for selector, block in reversed(group):
            m = re.search(r"--accent:\s*(#[0-9A-Fa-f]{6})", block)
            if m:
                value = m.group(1)
                r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
                assert b > r, f"{label} accent {value} is not blue-dominant"
                assert b >= g > r, (
                    f"{label} accent {value} is not on the blue-violet axis"
                )
                break
        else:
            pytest.fail(f"no effective --accent found for {key} mode")


def test_logo_halo_is_not_oversized():
    """The old halo was a 190px disc with a heavy glow; it read as dated."""
    m = re.search(r"\.empty-logo::before\{[^}]*width:(\d+)px", CSS)
    assert m, "empty-logo halo rule not found"
    assert int(m.group(1)) <= 150, (
        f"logo halo is {m.group(1)}px wide; the refined finish keeps it <=150px"
    )


def test_no_data_i18n_value_leaks_a_placeholder_token():
    """Regression: a `{0}` left in a value bound by a data-i18n* attribute renders
    literally, because applyLocaleToDOM() calls t(key) with no arguments and only
    t(key, arg) substitutes. A parameterised string must be interpolated in JS at
    the call site instead."""
    i18n = (STATIC / "i18n.js").read_text(encoding="utf-8")
    # keys bound via data-i18n* in the markup
    bound = set(re.findall(r'data-i18n(?:-title|-placeholder|-aria-label)?="([A-Za-z0-9_]+)"', HTML))
    assert bound, "no data-i18n bindings found in index.html"
    values = dict(
        re.findall(r"^\s*([A-Za-z0-9_]+):\s*'((?:\\.|[^'\\])*)'", i18n, re.M)
    )
    offenders = [k for k in sorted(bound) if "{" in values.get(k, "")]
    assert not offenders, (
        f"these keys are bound by data-i18n* but contain a substitution token, so "
        f"applyLocaleToDOM() will render it literally: {offenders}"
    )


EMPTY_TITLE_KEYS = [
    "tasks_empty_title", "skills_empty_title", "memory_empty_title",
    "workspaces_empty_title", "profiles_empty_title",
]


@pytest.mark.parametrize("title_key", EMPTY_TITLE_KEYS)
def test_empty_state_cta_is_wired_to_a_real_function(title_key):
    idx = HTML.find(f'data-i18n="{title_key}"')
    assert idx != -1, f"empty-state title {title_key} not found"
    window = HTML[idx:idx + 700]
    cta = re.search(r'class="empty-cta"[^>]*onclick="([A-Za-z_$][\w$]*)\(', window)
    if cta is None:
        # A selection-only empty state legitimately has no CTA.
        assert "memory" in title_key, (
            f"{title_key} is a creation-capable panel but has no primary CTA"
        )
        return
    fn = cta.group(1)
    assert re.search(rf"function\s+{re.escape(fn)}\s*\(", BUNDLE), (
        f"empty-state CTA calls {fn}(), which is not defined anywhere — the button "
        "would throw"
    )
    # A CTA must do real work, not just switchPanel() back to the panel the user
    # is already looking at. Only a genuine creation entry point is acceptable.
    assert fn not in {"switchPanel", "loadSkills", "loadMemory", "loadProfiles"}, (
        f"{title_key} CTA calls {fn}(), which only re-renders the current panel — "
        "a dead button that looks actionable"
    )
