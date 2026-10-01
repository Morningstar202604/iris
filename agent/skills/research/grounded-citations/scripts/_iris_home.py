"""Resolve IRIS_HOME for standalone skill scripts.

Skill scripts may run outside the Iris process (system Python, nix env,
CI) where ``iris_constants`` is not importable.  This module provides the
same ``get_iris_home()`` contract without requiring it on ``sys.path``.

When ``iris_constants`` IS available it is used directly so profile
resolution and any future enhancements are picked up automatically.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from iris_constants import get_iris_home as get_iris_home
except (ModuleNotFoundError, ImportError):

    def get_iris_home() -> Path:
        """Return the Iris home directory (default: ``~/.iris``)."""
        val = os.environ.get("IRIS_HOME", "").strip()
        return Path(val) if val else Path.home() / ".iris"
