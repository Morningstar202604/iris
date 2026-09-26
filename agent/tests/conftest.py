"""Shared isolation for the agent test suite.

`agent/AGENTS.md` requires tests to redirect `HERMES_HOME`; without this
fixture every test would read and write the operator's real home directory.
Also clears the profile home-key cache so a moved temp home is re-resolved.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_hermes_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes-home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(home))

    from hermes_constants import reset_hermes_home_key_cache

    reset_hermes_home_key_cache()
    yield home
    reset_hermes_home_key_cache()
