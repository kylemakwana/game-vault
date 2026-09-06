import importlib


def test_config_imports_without_psn_npsso(monkeypatch):
    monkeypatch.delenv("PSN_NPSSO", raising=False)

    from game_vault import config

    importlib.reload(config)

    assert config.Platform.PLAYSTATION == "PlayStation"


def test_playstation_console_values():
    from game_vault.config import PlayStationConsole

    assert PlayStationConsole.PS5 == "PS5"
    assert PlayStationConsole.PS4 == "PS4"
    assert PlayStationConsole.PS3 == "PS3"
    assert PlayStationConsole.PS_UNKNOWN == "Unknown PlayStation console"
