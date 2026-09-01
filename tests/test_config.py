import importlib
import sys


def test_config_loads_psn_npsso_from_environment(monkeypatch):
    monkeypatch.setenv("PSN_NPSSO", "test-token")
    sys.modules.pop("game_vault.config", None)

    config = importlib.import_module("game_vault.config")

    assert config.PSN_NPSSO == "test-token"


def test_playstation_console_values():
    from game_vault.config import PlayStationConsole

    assert PlayStationConsole.PS5 == "PS5"
    assert PlayStationConsole.PS4 == "PS4"
    assert PlayStationConsole.PS3 == "PS3"
    assert PlayStationConsole.PS_UNKNOWN == "Unknown PlayStation console"
