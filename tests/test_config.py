import importlib


def test_config_imports_without_psn_npsso(monkeypatch):
    monkeypatch.delenv("PSN_NPSSO", raising=False)

    from game_vault import config

    importlib.reload(config)

    assert config.PlatformEnum.PLAYSTATION == "PlayStation"


def test_playstation_console_values():
    from game_vault.config import PlayStationPlatformEnum

    assert PlayStationPlatformEnum.PS5 == "PS5"
    assert PlayStationPlatformEnum.PS4 == "PS4"
    assert PlayStationPlatformEnum.PS3 == "PS3"
    assert PlayStationPlatformEnum.PSPC == "PSPC"
    assert PlayStationPlatformEnum.PSVITA == "PSVITA"
    assert PlayStationPlatformEnum.UNKNOWN == "Unknown PlayStation console"


def test_playstation_title_categories():
    from game_vault.config import PlayStationTitleCategoryEnum

    assert PlayStationTitleCategoryEnum.PS5_NATIVE_GAME == "ps5_native_game"
    assert PlayStationTitleCategoryEnum.PS4_GAME == "ps4_game"
    assert PlayStationTitleCategoryEnum.UNKNOWN == "unknown"
