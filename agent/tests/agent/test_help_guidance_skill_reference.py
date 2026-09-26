"""Contract: the skill pointer inside the stable help guidance must resolve.

`system_prompt.build_system_prompt_parts` only swaps in HERMES_AGENT_HELP_GUIDANCE
when the referenced skill actually renders in the skills index, so the name the
guidance tells the model to load must appear there as `- <name>:` — otherwise the
prompt teaches the model a call that cannot succeed.
"""

from __future__ import annotations

import re
from pathlib import Path

import agent.prompt_builder as pb


def _bundled_skills_dir() -> Path:
    return Path(pb.__file__).resolve().parent.parent / "skills"


def test_help_guidance_skill_pointer_resolves_in_bundled_index():
    match = re.search(r"skill_view\(name='([^']+)'\)", pb.HERMES_AGENT_HELP_GUIDANCE)
    assert match, "guidance must name a skill_view target"
    name = match.group(1)

    index = pb.build_skills_system_prompt(skills_dir_override=_bundled_skills_dir())

    assert f"- {name}:" in index, (
        f"guidance points the model at skill_view(name={name!r}) "
        f"but no such entry renders in the bundled skills index"
    )


def test_no_skills_variant_carries_no_skill_pointer():
    assert "skill_view" not in pb.HERMES_AGENT_HELP_GUIDANCE_NO_SKILLS
