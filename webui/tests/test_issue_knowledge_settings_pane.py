"""Regression: the settings 知识库 section never activated settingsPaneKnowledge.

switchSettingsSection()'s pane-activation loop iterated
['conversation','appearance','preferences','providers','plugins','extensions','system','help']
and the companion section->pane `map` omitted 'knowledge' as well, so clicking
知识库 highlighted the sidebar item but the pane never received `.active`;
loadKnowledgePanel() then populated a hidden pane. Live CDP evidence:
menu active=True, settingsPaneKnowledge.offsetParent=None, kb empty-state text
already rendered. The scheduled-jobs banner also told users to run `iris gateway`,
which is not an installed entry point (pyproject [project.scripts] ships only
hermes / hermes-agent / hermes-acp).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANELS_JS = (ROOT / "static" / "panels.js").read_text(encoding="utf-8")
I18N_JS = (ROOT / "static" / "i18n.js").read_text(encoding="utf-8")
INDEX_HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _switch_settings_section_body():
    start = PANELS_JS.index("function switchSettingsSection(")
    end = PANELS_JS.index("\nfunction ", start + 1)
    return PANELS_JS[start:end]


def test_pane_activation_array_includes_knowledge():
    body = _switch_settings_section_body()
    m = re.search(r"\[('conversation'[^\]]*)\]\.forEach\(key=>\{", body)
    assert m, "pane-activation forEach array not found in switchSettingsSection"
    keys = [k.strip().strip("'") for k in m.group(1).split(",")]
    assert "knowledge" in keys, (
        "settingsPaneKnowledge never receives .active: 'knowledge' missing "
        f"from pane-activation array (found {keys})"
    )


def test_map_includes_knowledge():
    body = _switch_settings_section_body()
    m = re.search(r"const map=\{([^}]*)\}", body)
    assert m, "section->pane map not found in switchSettingsSection"
    assert "knowledge:'Knowledge'" in m.group(1).replace(" ", ""), (
        "map lacks knowledge entry; $('settingsPane'+map[key]) resolution "
        "for the knowledge section is undefined"
    )


def test_knowledge_nav_button_and_pane_present():
    assert 'data-settings-section="knowledge"' in INDEX_HTML
    assert 'id="settingsPaneKnowledge"' in INDEX_HTML
    assert "loadKnowledgePanel()" in PANELS_JS


def test_gateway_hint_references_installed_command():
    # The scheduled-jobs hint copy now lives in the i18n bundles (it is
    # user-facing chrome), so search both the renderer and the bundles — the
    # intent is that the hint names a command that actually exists.
    haystack = PANELS_JS + I18N_JS
    assert "`iris gateway`" not in haystack, (
        "no `iris` entry point is installed (pyproject [project.scripts]: "
        "hermes / hermes-agent / hermes-acp); the scheduled-jobs hint must "
        "stay executable"
    )
    assert "`hermes gateway`" in haystack
