"""IRIS_HOME is the primary home env var; HERMES_HOME remains as fallback.

The product is Iris, so the user-facing configuration surface takes IRIS_HOME;
existing deployments and upstream tooling keep working through HERMES_HOME.
"""

from __future__ import annotations

import hermes_constants as hc


def test_iris_home_takes_precedence_over_hermes_home(monkeypatch, tmp_path):
    iris = tmp_path / "iris-home"
    hermes = tmp_path / "hermes-home"
    monkeypatch.setenv("IRIS_HOME", str(iris))
    monkeypatch.setenv("HERMES_HOME", str(hermes))
    hc.reset_hermes_home_key_cache()

    assert hc.get_process_hermes_home() == iris
    assert hc.get_hermes_home() == iris


def test_hermes_home_remains_as_fallback(monkeypatch, tmp_path):
    hermes = tmp_path / "hermes-home"
    monkeypatch.delenv("IRIS_HOME", raising=False)
    monkeypatch.setenv("HERMES_HOME", str(hermes))
    hc.reset_hermes_home_key_cache()

    assert hc.get_process_hermes_home() == hermes
    assert hc.get_hermes_home() == hermes


def test_blank_iris_home_falls_through_to_hermes_home(monkeypatch, tmp_path):
    hermes = tmp_path / "hermes-home"
    monkeypatch.setenv("IRIS_HOME", "   ")
    monkeypatch.setenv("HERMES_HOME", str(hermes))
    hc.reset_hermes_home_key_cache()

    assert hc.get_process_hermes_home() == hermes
