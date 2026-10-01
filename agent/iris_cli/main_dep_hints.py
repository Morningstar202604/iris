"""Plain-language copy for surfaces that cannot start because an optional dependency group is missing.

``iris dashboard`` (fastapi + uvicorn) and ``iris acp`` (agent-client-protocol) are installed by
the ``[all]`` / ``[acp]`` extras. A partial install, a pip-less uv venv or an interrupted update can
leave them out; the built-in repair is ``iris update``, which reinstalls the extras into the same
interpreter. The manual fallback names the checkout directory and interpreter explicitly because a bare
``pip install -e '.[acp]'`` fails on PEP 668 systems and in venvs without pip.
"""

import sys


def missing_optional_deps_message(surface: str, what: str, extra: str) -> str:
    """``surface`` = "dashboard"/"ACP server"; ``what`` = "its web-server packages"; ``extra`` = "all"/"acp"."""
    from iris_cli.main import PROJECT_ROOT

    return (
        f"The {surface} can't start: {what} are missing from this install.\n"
        "Run `iris update` to reinstall dependencies. If that fails, run manually:\n"
        f"  cd {PROJECT_ROOT} && {sys.executable} -m pip install -e '.[{extra}]'\n"
        f"  (no pip in this venv: uv pip install -e '.[{extra}]')"
    )
