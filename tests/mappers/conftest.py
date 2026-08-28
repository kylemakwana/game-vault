from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from game_vault.mappers.playstation_mapper import PlaystationMapper


@pytest.fixture
def account_snapshot():
    return SimpleNamespace(
        account_id="123456789",
        online_id="TestPlayer",
        avatar_url="https://example.com/avatar.png",
    )


@pytest.fixture
def played_title():
    return SimpleNamespace(
        title_id="CUSA00001",
        content_type="game",
        play_duration_seconds=7200,
        play_count=4,
        first_played_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        last_played_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
    )


@pytest.fixture
def trophy():
    return SimpleNamespace(
        trophy_id=1,
        name="First Trophy",
        detail="Earn your first trophy",
        icon_url="https://example.com/trophy.png",
        hidden=False,
        type="bronze",
        rarity="common",
        earn_rate=75.5,
        progress_target_value=None,
        user_progress=SimpleNamespace(
            earned=True,
            earned_at=datetime(2025, 1, 5, tzinfo=timezone.utc),
            progress=None,
            progress_rate=100.0,
            progressed_at=datetime(2025, 1, 5, tzinfo=timezone.utc),
        ),
    )


@pytest.fixture
def trophy_group(trophy):
    return SimpleNamespace(
        group_id="default",
        name="Base Game",
        trophies=[trophy],
    )


@pytest.fixture
def trophy_title(trophy_group):
    return SimpleNamespace(
        np_communication_id="NPWR00001_00",
        title_name="Test Game",
        groups=[trophy_group],
    )


@pytest.fixture
def snapshot(account_snapshot, played_title, trophy_title):
    return SimpleNamespace(
        account=account_snapshot,
        played_titles=[played_title],
        trophy_titles=[trophy_title],
    )


@pytest.fixture
def game():
    return SimpleNamespace(
        id="test-game",
        name="Test Game",
    )


@pytest.fixture
def unrelated_game():
    return SimpleNamespace(
        id="other-game",
        name="Other Game",
    )


@pytest.fixture
def release(game):
    return SimpleNamespace(
        id="test-game-ps5",
        game_id=game.id,
    )


@pytest.fixture
def unrelated_release(unrelated_game):
    return SimpleNamespace(
        id="other-game-ps5",
        game_id=unrelated_game.id,
    )


@pytest.fixture
def title_mapping(release):
    return SimpleNamespace(
        source="playstation_title",
        source_id="CUSA00001",
        game_release_id=release.id,
    )


@pytest.fixture
def trophy_mapping(release):
    return SimpleNamespace(
        source="playstation_trophy_set",
        source_id="NPWR00001_00",
        game_release_id=release.id,
    )


@pytest.fixture
def game_series():
    return SimpleNamespace(
        id="test-series",
        name="Test Series",
    )


@pytest.fixture
def series_membership(game, game_series):
    return SimpleNamespace(
        game_id=game.id,
        series_id=game_series.id,
    )


@pytest.fixture
def mapper(
    snapshot,
    title_mapping,
    trophy_mapping,
    release,
    unrelated_release,
    game,
    unrelated_game,
    game_series,
    series_membership,
):
    return PlaystationMapper(
        snapshot=snapshot,
        mappings=[title_mapping, trophy_mapping],
        releases=[release, unrelated_release],
        games=[game, unrelated_game],
        series=[game_series],
        series_memberships=[series_membership],
    )
