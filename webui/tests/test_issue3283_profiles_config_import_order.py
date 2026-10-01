"""Regression coverage for #3283 profile/config import ordering.

Importing ``api.profiles`` before ``api.config`` used to trigger a circular import
through ``profiles._resolve_base_iris_home() -> api.config``. ``api.config``
then caught the partial-module ``ImportError`` from its startup
``init_profile_state`` import, so the later config import never initialized the
sticky active profile.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_profiles_first_then_config_still_initializes_active_profile(tmp_path):
    home = tmp_path / "home"
    base = home / ".iris"
    profile_home = base / "profiles" / "webui"
    profile_home.mkdir(parents=True)
    (base / "active_profile").write_text("webui", encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("IRIS_HOME", None)
    env.pop("IRIS_BASE_HOME", None)
    env.pop("IRIS_WEBUI_STATE_DIR", None)
    env["HOME"] = str(home)
    env["PYTHONPATH"] = str(repo_root)

    code = """
import os
import api.profiles
import api.config
print(os.environ.get('IRIS_HOME', ''))
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == str(profile_home)
