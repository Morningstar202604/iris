"""Regression: shipped UI chrome must be localized in both directions.

The app mixed languages because user-visible copy bypasses i18n entirely —
hardcoded Chinese (so English mode showed Chinese) and hardcoded English (so
Chinese mode showed "Sessions" / "Light" / "Default"). These tests encode the
invariant that chrome goes through ``t()`` / ``data-i18n`` and that the Chinese
bundle is complete, so the mixing cannot come back.

Skill names, skill descriptions, model names and plugin/provider manifests are
data rather than chrome, so they are deliberately out of scope: translating a
skill's own metadata would be wrong.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
I18N = (STATIC / "i18n.js").read_text(encoding="utf-8")
INDEX_HTML = (STATIC / "index.html").read_text(encoding="utf-8")
PANELS_JS = (STATIC / "panels.js").read_text(encoding="utf-8")
PALETTE_JS = (STATIC / "command-palette.js").read_text(encoding="utf-8")

CJK = re.compile(r"[\u4e00-\u9fff]")
STRING_LITERAL = re.compile(r"""(['"`])((?:\\.|(?!\1).)*?)\1""", re.S)
COMMENT_LINE = re.compile(r"^\s*(//|\*|/\*)")

# Opt-out marker for literals that contain CJK on purpose and are NOT displayed
# copy — e.g. the multilingual keyword vocabulary used to recognise "continue"
# in any language. Localizing those would break the matching, so the author must
# mark the line explicitly and the exemption stays reviewable in the diff.
EXEMPT_MARKER = "aqg-i18n-exempt"

# Front-end files whose user-visible copy must be localized. Skill/plugin
# manifests and skill descriptions are data, not chrome, so they are not here.
# sw.js is excluded on purpose: a service worker has no access to the page's
# i18n runtime, so it carries its own offline copy and is checked separately by
# test_service_worker_offline_page_is_localized.
CHROME_JS = [
    "boot.js",
    "command-palette.js",
    "commands.js",
    "messages.js",
    "onboarding.js",
    "panels.js",
    "ui.js",
]

# Locales that must be complete. Other bundles fall back to English by design
# (i18n.js:4) — machine-translating them is worse than a clean English string.
REQUIRED_LOCALES = ["en", "zh"]


def _locale_keys():
    lines = I18N.splitlines()
    starts = [
        (i, m.group(1).strip("'"))
        for i, line in enumerate(lines)
        if (m := re.match(r"^  ('?[A-Za-z0-9_\-]+'?):\s*\{\s*$", line))
    ]
    keys = {}
    for idx, (start, name) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        # start + 1 skips the block's own `name: {` header, which would otherwise
        # be parsed as a translation key named after the locale.
        body = "\n".join(lines[start + 1:end])
        keys[name] = set(re.findall(r"^\s*([A-Za-z0-9_]+):", body, re.M))
    return keys


LOCALE_KEYS = _locale_keys()
EN_KEYS = LOCALE_KEYS["en"]


def _hardcoded_cjk_lines(path):
    hits = []
    for lineno, line in enumerate(
        (STATIC / path).read_text(encoding="utf-8").splitlines(), 1
    ):
        if not CJK.search(line) or COMMENT_LINE.match(line):
            continue
        if EXEMPT_MARKER in line:
            continue
        for match in STRING_LITERAL.finditer(line):
            text = match.group(2)
            if CJK.search(text) and len(text.strip()) > 1:
                hits.append(f"{path}:{lineno} {text.strip()[:60]!r}")
                break
    return hits


@pytest.mark.parametrize("path", CHROME_JS)
def test_no_hardcoded_cjk_in_chrome_js(path):
    assert not _hardcoded_cjk_lines(path), (
        "user-visible copy must go through t(); hardcoded CJK breaks non-Chinese "
        f"locales: {_hardcoded_cjk_lines(path)}"
    )


@pytest.mark.parametrize("locale", REQUIRED_LOCALES)
def test_locale_bundle_is_complete(locale):
    missing = sorted(EN_KEYS - LOCALE_KEYS[locale])
    assert not missing, (
        f"{locale} bundle is missing {len(missing)} keys defined in en: {missing[:20]}"
    )


def _titlebar_map():
    match = re.search(
        r"APP_TITLEBAR_KEYS\s*=\s*\{(.*?)\}", PANELS_JS, re.S
    )
    assert match, "APP_TITLEBAR_KEYS map not found in panels.js"
    return dict(re.findall(r"([A-Za-z0-9_]+)\s*:\s*'([A-Za-z0-9_]+)'", match.group(1)))


def _rail_panels():
    return sorted(set(re.findall(r'data-panel="([A-Za-z0-9_-]+)"', INDEX_HTML)))


def test_every_rail_panel_has_a_titlebar_key():
    titlebar = _titlebar_map()
    missing = [p for p in _rail_panels() if p not in titlebar]
    assert not missing, (
        f"panels without an APP_TITLEBAR_KEYS entry fall back to a capitalized "
        f"English panel name in every locale: {missing}"
    )


def test_titlebar_keys_resolve_in_required_locales():
    titlebar = _titlebar_map()
    for panel, key in titlebar.items():
        for locale in REQUIRED_LOCALES:
            assert key in LOCALE_KEYS[locale], (
                f"panel {panel!r} maps to {key!r} which the {locale} bundle "
                "does not define"
            )


def test_service_worker_offline_page_is_localized():
    # The SW cannot import i18n.js, so it must ship its own copy for every locale
    # it claims to support and must not render one hardcoded language.
    sw = (STATIC / "sw.js").read_text(encoding="utf-8")
    block = re.search(r"const OFFLINE_COPY = \{(.*?)\n\};", sw, re.S)
    assert block, "sw.js must define OFFLINE_COPY for the offline page"
    for locale in ("en", "zh", "'zh-Hant'"):
        assert re.search(rf"(?:^|\n)\s*{locale}:\s*\{{", block.group(1)), (
            f"sw.js offline copy is missing the {locale} locale"
        )
    for field in ("title", "detail"):
        assert len(re.findall(rf"{field}:\s*'", block.group(1))) == 3, (
            f"every offline locale needs a {field}"
        )
    assert "navigator.language" in sw, (
        "the SW must choose its language from navigator.language rather than "
        "hardcoding one"
    )
    assert "offlinePageHtml()" in sw, "the offline response must use the localized page"


def test_no_unconditional_hardcoded_offline_body():
    # Guards the specific regression: an English <h2> next to a Chinese <p>.
    sw = (STATIC / "sw.js").read_text(encoding="utf-8")
    body = re.search(r"return caches\.match\('\./'\).*?\)\);", sw, re.S)
    assert body, "offline fallback response not found"
    assert "You are offline" not in body.group(0) and "需要连接服务器" not in body.group(0), (
        "offline response must not inline a single language"
    )


def test_command_palette_settings_action_is_not_dead_code():
    # A `typeof <name>==='function'` guard on a name that is never defined makes
    # the action a silent no-op, so the palette item must reference a real global.
    # The definitions live in sibling scripts (these are shared globals), so the
    # lookup has to span the whole static bundle, not just the palette file.
    bundle = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(STATIC.glob("*.js"))
    ) + INDEX_HTML
    dead = re.findall(r"typeof\s+([A-Za-z_$一-鿿]+)\s*===\s*'function'", PALETTE_JS)
    assert dead, "expected the palette to guard some global actions"
    for name in dead:
        defined = re.search(rf"function\s+{re.escape(name)}\s*\(", bundle) or re.search(
            rf"(?:window|var|let|const)\s+{re.escape(name)}\s*=", bundle
        )
        assert defined, (
            f"command palette guards a never-defined {name!r}; that action is a "
            "silent no-op for users"
        )
