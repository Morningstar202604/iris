"""IRIS_HOME is the primary home env var.

The product is Iris; the user-facing configuration surface takes IRIS_HOME.
"""

from __future__ import annotations

import iris_constants as hc


def test_iris_home_is_read(monkeypatch, tmp_path):
    iris = tmp_path / "iris-home"
    monkeypatch.setenv("IRIS_HOME", str(iris))
    hc.reset_iris_home_key_cache()

    assert hc.get_process_iris_home() == iris
    assert hc.get_iris_home() == iris


def test_iris_home_defaults_to_platform_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("IRIS_HOME", raising=False)
    hc.reset_iris_home_key_cache()

    assert hc.get_iris_home() == hc._get_platform_default_iris_home()


def test_blank_iris_home_falls_through_to_default(monkeypatch, tmp_path):
    monkeypatch.setenv("IRIS_HOME", "   ")
    hc.reset_iris_home_key_cache()

    assert hc.get_process_iris_home() == hc._get_platform_default_iris_home()
