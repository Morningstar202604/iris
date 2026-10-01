"""Regression coverage for pytest isolation of Iris config paths."""
import os
from pathlib import Path


def test_pytest_overrides_inherited_iris_config_path():
    """A live-agent IRIS_CONFIG_PATH must never leak into WebUI tests.

    Iris agents commonly run with IRIS_CONFIG_PATH pointing at the real
    ~/.iris/config.yaml. The test harness must replace it with the isolated
    test home before product modules are imported, otherwise provider/onboarding
    tests can mutate the user's real config.
    """
    test_state_dir = Path(os.environ["IRIS_WEBUI_TEST_STATE_DIR"])
    assert Path(os.environ["IRIS_CONFIG_PATH"]) == test_state_dir / "config.yaml"
