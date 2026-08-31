import importlib
import sys


def test_config_loads_psn_npsso_from_environment(monkeypatch):
    monkeypatch.setenv("PSN_NPSSO", "test-token")
    sys.modules.pop("game_vault.config", None)

    config = importlib.import_module("game_vault.config")

    assert config.PSN_NPSSO == "test-token"
