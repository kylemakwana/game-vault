from types import SimpleNamespace

import pytest

from game_vault.config import Platform


def test_find_release_mapping_returns_matching_mapping(
    mapper,
    title_mapping,
):
    result = mapper._find_release_mapping(
        source_id="CUSA00001",
        source="playstation_title",
    )

    assert result is title_mapping


def test_find_release_mapping_returns_none_when_not_found(mapper):
    result = mapper._find_release_mapping(
        source_id="UNKNOWN",
        source="playstation_title",
    )

    assert result is None


def test_mapped_releases_only_returns_releases_with_mapping(
    mapper,
    release,
):
    result = mapper._mapped_releases()

    assert result == [release]


def test_mapped_games_only_returns_games_for_mapped_releases(
    mapper,
    game,
):
    result = mapper._mapped_games()

    assert result == [game]


def test_mapped_series_memberships_only_returns_memberships_for_mapped_games(
    mapper,
    game,
    series_membership,
):
    result = mapper._mapped_series_memberships([game])

    assert result == [series_membership]


def test_mapped_series_returns_series_for_memberships(
    mapper,
    game_series,
    series_membership,
):
    result = mapper._mapped_series([series_membership])

    assert result == [game_series]


def test_map_account(mapper):
    result = mapper._map_account()

    assert result.id == "psn:123456789"
    assert result.service_id == Platform.PLAYSTATION
    assert result.username == "TestPlayer"
    assert result.external_account_id == "123456789"
    assert result.avatar_url == "https://example.com/avatar.png"


def test_map_played_titles(mapper):
    account = mapper._map_account()

    result = mapper._map_played_titles(account)

    assert len(result) == 1

    activity = result[0]

    assert activity.id == "psn-activity:CUSA00001"
    assert activity.account_id == account.id
    assert activity.game_release_id == "test-game-ps5"
    assert activity.playtime_seconds == 7200
    assert activity.play_count == 4
    assert activity.source == Platform.PLAYSTATION


def test_map_played_titles_ignores_non_games(
    mapper,
):
    mapper.snapshot.played_titles = [
        SimpleNamespace(
            title_id="APP00001",
            content_type="app",
        )
    ]

    account = mapper._map_account()

    result = mapper._map_played_titles(account)

    assert result == []


def test_map_played_titles_ignores_title_without_mapping(
    mapper,
):
    mapper.snapshot.played_titles = [
        SimpleNamespace(
            title_id="UNKNOWN",
            content_type="game",
        )
    ]

    account = mapper._map_account()

    result = mapper._map_played_titles(account)

    assert result == []


def test_map_played_titles_ignores_mapping_without_release(
    mapper,
):
    mapper.mappings.append(
        SimpleNamespace(
            source="playstation_title",
            source_id="MISSING_RELEASE",
            game_release_id="does-not-exist",
        )
    )

    mapper.snapshot.played_titles = [
        SimpleNamespace(
            title_id="MISSING_RELEASE",
            content_type="game",
        )
    ]

    account = mapper._map_account()

    result = mapper._map_played_titles(account)

    assert result == []


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("ps5_native_game", "ps5"),
        ("ps4_game", "ps4"),
        ("unknown", "playstation_unknown"),
        ("ps3_game", "playstation_unknown"),
    ],
)
def test_platform_from_category(category, expected):
    from game_vault.mappers.playstation_mapper import PlayStationMapper

    result = PlayStationMapper._platform_from_category(category)

    assert result == expected


def test_map_trophy_title_returns_none_without_mapping(
    mapper,
):
    trophy_title = SimpleNamespace(
        np_communication_id="UNKNOWN",
    )

    account = mapper._map_account()

    result = mapper._map_trophy_title(
        trophy_title,
        account,
    )

    assert result is None


def test_map_trophy_title_creates_achievement_set(
    mapper,
    trophy_title,
):
    account = mapper._map_account()

    result = mapper._map_trophy_title(
        trophy_title,
        account,
    )

    achievement_set, groups, achievements, progress = result

    assert achievement_set.id == "psn-trophy-set:NPWR00001_00"
    assert achievement_set.game_release_id == "test-game-ps5"
    assert achievement_set.service_id == Platform.PLAYSTATION
    assert achievement_set.name == "Test Game"
    assert achievement_set.external_identifier == "NPWR00001_00"

    assert len(groups) == 1
    assert len(achievements) == 1
    assert len(progress) == 1


def test_map_trophy_title_creates_achievement_group(
    mapper,
    trophy_title,
):
    account = mapper._map_account()

    _, groups, _, _ = mapper._map_trophy_title(
        trophy_title,
        account,
    )

    group = groups[0]

    assert group.id == "psn-trophy-set:NPWR00001_00:default"
    assert group.achievement_set_id == "psn-trophy-set:NPWR00001_00"
    assert group.external_group_id == "default"
    assert group.name == "Base Game"


def test_map_trophy_title_creates_achievement(
    mapper,
    trophy_title,
):
    account = mapper._map_account()

    _, _, achievements, _ = mapper._map_trophy_title(
        trophy_title,
        account,
    )

    achievement = achievements[0]

    assert achievement.id == "psn-trophy-set:NPWR00001_00:1"
    assert achievement.achievement_set_id == "psn-trophy-set:NPWR00001_00"
    assert achievement.group_id == "psn-trophy-set:NPWR00001_00:default"
    assert achievement.external_id == "1"
    assert achievement.name == "First Trophy"
    assert achievement.description == "Earn your first trophy"
    assert achievement.icon_url == "https://example.com/trophy.png"
    assert achievement.hidden is False
    assert achievement.achievement_type == "bronze"
    assert achievement.rarity == "common"
    assert achievement.global_unlock_percentage == 75.5


def test_map_trophy_title_creates_achievement_progress(
    mapper,
    trophy_title,
):
    account = mapper._map_account()

    _, _, _, progress_records = mapper._map_trophy_title(
        trophy_title,
        account,
    )

    progress = progress_records[0]

    assert progress.achievement_id == "psn-trophy-set:NPWR00001_00:1"
    assert progress.account_id == account.id
    assert progress.unlocked is True
    assert progress.progress_percentage == 100.0


def test_map_trophy_titles_skips_unmapped_titles(
    mapper,
    trophy_title,
):
    mapper.snapshot.trophy_titles = [
        trophy_title,
        SimpleNamespace(
            np_communication_id="UNKNOWN",
        ),
    ]

    account = mapper._map_account()

    sets, groups, achievements, progress = mapper._map_trophy_titles(account)

    assert len(sets) == 1
    assert len(groups) == 1
    assert len(achievements) == 1
    assert len(progress) == 1


def test_map_returns_complete_mapped_data(
    mapper,
    game,
    release,
    game_series,
    series_membership,
):
    result = mapper.map()

    assert result.account.id == "psn:123456789"

    assert result.games == [game]
    assert result.releases == [release]

    assert result.series == [game_series]
    assert result.series_membership == [series_membership]

    assert len(result.activities) == 1

    assert len(result.achievement_sets) == 1
    assert len(result.achievement_groups) == 1
    assert len(result.achievements) == 1
    assert len(result.achievement_progress) == 1

    assert result.mappings == mapper.mappings
