from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from game_vault.collectors.playstation_collector import PlayStationCollector


@pytest.fixture
def mock_psn_client() -> Mock:
    return Mock()


@pytest.fixture
def mock_playstation_collector(mock_psn_client, tmp_path) -> PlayStationCollector:
    return PlayStationCollector(
        client=mock_psn_client,
        raw_dir=tmp_path,
    )


@pytest.fixture
def mock_trophy_title() -> SimpleNamespace:
    return SimpleNamespace(
        np_communication_id="TEST12345_00",
        title_name="Test Game",
        title_platform={"PS5"},
    )
