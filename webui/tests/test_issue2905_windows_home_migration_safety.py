"""Regression coverage for #2905 — Windows upgrade stranding WebUI state.

v0.51.134 (PR #2897) moved the Windows default Iris home from
``%USERPROFILE%\\.iris`` to ``%LOCALAPPDATA%\\iris`` to match the agent.
Upgrading users whose WebUI sessions/pins/settings still lived at the old
location opened the app to an empty state — the data was intact on disk but at
an address the new build no longer read.

The fix makes ``_platform_default_iris_home()`` prefer the populated legacy
``%USERPROFILE%\\.iris`` ONLY when the new ``%LOCALAPPDATA%\\iris`` location
is not yet established. It is:
  * non-destructive — no files are moved (a move would be its own data-loss risk)
  * self-healing — affected users find their data on next launch, no action needed
  * surgical — fresh installs / already-migrated users / explicit overrides are
    completely unaffected.

These tests fake Windows semantics on a POSIX CI host by swapping ``config.os``
for a shim whose ``name`` is ``'nt'`` and pointing HOME / LOCALAPPDATA at temp
dirs. They assert the full truth table plus the no-regression guards.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

import api.config as config
import api.paths as paths


class _WindowsOSShim:
    """Stand-in for the ``os`` module that reports ``name == 'nt'``."""

    name = "nt"
    environ = os.environ

    def __getattr__(self, key):  # delegate everything else to the real os
        return getattr(os, key)

    def getenv(self, *args, **kwargs):
        return os.getenv(*args, **kwargs)


def _populate_webui_state(base: Path) -> None:
    (base / "webui" / "sessions").mkdir(parents=True, exist_ok=True)
    (base / "webui" / "settings.json").write_text('{"pinned":["a"]}', encoding="utf-8")
    (base / "config.yaml").write_text("model: x\n", encoding="utf-8")


@pytest.fixture
def windows_env(monkeypatch, tmp_path):
    """Yield (legacy_home, new_home) with Windows path semantics faked.

    Returns the two candidate base homes; the caller populates whichever it
    needs before calling ``config._platform_default_iris_home()``.
    """
    home = tmp_path / "userprofile"          # %USERPROFILE%
    localappdata = tmp_path / "localappdata" # %LOCALAPPDATA%
    home.mkdir()
    localappdata.mkdir()

    legacy_home = home / ".iris"
    new_home = localappdata / "iris"

    monkeypatch.setattr(paths, "HOME", home)
    monkeypatch.setattr(paths, "os", _WindowsOSShim())
    monkeypatch.setenv("LOCALAPPDATA", str(localappdata))
    monkeypatch.delenv("IRIS_HOME", raising=False)
    monkeypatch.delenv("IRIS_BASE_HOME", raising=False)

    return legacy_home, new_home


def test_upgrade_fingerprint_prefers_populated_legacy_home(windows_env):
    """The #2905 bug case: legacy populated, new empty → resolve to legacy."""
    legacy_home, new_home = windows_env
    _populate_webui_state(legacy_home)
    # new_home intentionally left empty

    result = config._platform_default_iris_home()

    assert result == legacy_home, (
        "Windows upgrade must not strand WebUI state: when %LOCALAPPDATA%/iris "
        "is empty but %USERPROFILE%/.iris holds the user's sessions/pins, the "
        "default home must resolve to the legacy location (#2905)."
    )


def test_fresh_install_uses_new_localappdata_home(windows_env):
    """Neither location populated → use the new %LOCALAPPDATA% default (no regression on #2840)."""
    legacy_home, new_home = windows_env
    # both empty

    result = config._platform_default_iris_home()

    assert result == new_home


def test_already_migrated_uses_new_home(windows_env):
    """New location populated → never reach back to legacy."""
    legacy_home, new_home = windows_env
    _populate_webui_state(new_home)

    result = config._platform_default_iris_home()

    assert result == new_home


def test_both_populated_trusts_new_home(windows_env):
    """If both exist, the new location wins — we never silently divert an
    established %LOCALAPPDATA% install back to a stale legacy dir."""
    legacy_home, new_home = windows_env
    _populate_webui_state(legacy_home)
    _populate_webui_state(new_home)

    result = config._platform_default_iris_home()

    assert result == new_home


def test_legacy_dir_present_but_empty_does_not_divert(windows_env):
    """An empty/initialized-but-stateless legacy dir must NOT trigger the
    fallback — otherwise a stray empty %USERPROFILE%/.iris would shadow a
    fresh install."""
    legacy_home, new_home = windows_env
    legacy_home.mkdir(parents=True)  # exists but no webui/config/auth markers

    result = config._platform_default_iris_home()

    assert result == new_home


def test_does_nothing_on_posix(monkeypatch, tmp_path):
    """On POSIX (os.name != 'nt') the resolver always returns ~/.iris,
    regardless of any LOCALAPPDATA value — the fix is Windows-only."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(paths, "HOME", home)
    monkeypatch.setattr(paths, "os", os)
    # real os.name is 'posix' on CI; do NOT swap in the Windows shim
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "lad"))
    monkeypatch.delenv("IRIS_HOME", raising=False)

    result = config._platform_default_iris_home()

    assert result == home / ".iris"


def test_no_files_are_moved_by_resolution(windows_env):
    """The fix is non-destructive: resolving the home must not create, move,
    or delete anything at either location."""
    legacy_home, new_home = windows_env
    _populate_webui_state(legacy_home)
    legacy_sessions = legacy_home / "webui" / "sessions"
    before_new_exists = new_home.exists()

    config._platform_default_iris_home()

    # Legacy data untouched, new location not fabricated.
    assert legacy_sessions.is_dir()
    assert (legacy_home / "webui" / "settings.json").exists()
    assert new_home.exists() == before_new_exists


class TestIrisHomeHasWebuiState:
    """Unit coverage for the marker-detection helper."""

    def test_empty_or_missing_dir_is_not_state(self, tmp_path):
        assert paths._iris_home_has_webui_state(tmp_path / "nope") is False
        empty = tmp_path / "empty"
        empty.mkdir()
        assert paths._iris_home_has_webui_state(empty) is False

    def test_webui_sessions_marker_counts(self, tmp_path):
        (tmp_path / "webui" / "sessions").mkdir(parents=True)
        assert paths._iris_home_has_webui_state(tmp_path) is True

    def test_webui_settings_marker_counts(self, tmp_path):
        (tmp_path / "webui").mkdir()
        (tmp_path / "webui" / "settings.json").write_text("{}", encoding="utf-8")
        assert paths._iris_home_has_webui_state(tmp_path) is True

    def test_webui_dir_alone_counts(self, tmp_path):
        (tmp_path / "webui").mkdir()
        assert paths._iris_home_has_webui_state(tmp_path) is True

    def test_agent_only_artifacts_do_not_count(self, tmp_path):
        """A home with ONLY agent files (config.yaml / auth.json) and no webui/
        dir is NOT treated as WebUI state — otherwise a long-time agent user
        installing WebUI fresh would be wrongly diverted to the legacy dir."""
        (tmp_path / "config.yaml").write_text("model: x\n", encoding="utf-8")
        (tmp_path / "auth.json").write_text("{}", encoding="utf-8")
        assert paths._iris_home_has_webui_state(tmp_path) is False


def test_profiles_base_home_uses_shared_path_helper(monkeypatch, tmp_path):
    """profiles._resolve_base_iris_home() must share config's path helper so
    the active-profile pointer never diverges from config.STATE_DIR (#2905)."""
    import api.profiles as profiles

    sentinel = tmp_path / "sentinel-home"
    monkeypatch.delenv("IRIS_HOME", raising=False)
    monkeypatch.delenv("IRIS_BASE_HOME", raising=False)
    monkeypatch.setattr(paths, "_platform_default_iris_home", lambda: sentinel)

    assert profiles._resolve_base_iris_home() == sentinel
