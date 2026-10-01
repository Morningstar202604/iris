"""Resolve IRIS_HOME for standalone skill scripts.

Skill scripts may run outside the Iris process (e.g. system Python,
nix env, CI) where ``iris_constants`` is not importable.  This module
provides the same ``get_iris_home()`` and ``display_iris_home()``
contracts as ``iris_constants`` without requiring it on ``sys.path``.

When ``iris_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``iris_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``IRIS_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from iris_constants import display_iris_home as display_iris_home
    from iris_constants import get_iris_home as get_iris_home
except (ModuleNotFoundError, ImportError):

    def get_iris_home() -> Path:
        """Return the Iris home directory (default: ~/.iris).

        Mirrors ``iris_constants.get_iris_home()``."""
        val = os.environ.get("IRIS_HOME", "").strip()
        return Path(val) if val else Path.home() / ".iris"

    def display_iris_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``iris_constants.display_iris_home()``."""
        home = get_iris_home()
        try:
            return "~/" + home.relative_to(Path.home()).as_posix()
        except ValueError:
            return str(home)
