import json
from datetime import UTC

import pytest

from game_vault.services.playstation_snapshot_builder import PlayStationSnapshotBuilder


def test_read_json(tmp_path):
    path = tmp_path / "test.json"

    path.write_text(
        json.dumps({"hello": "world"}),
        encoding="utf-8",
    )

    result = PlayStationSnapshotBuilder._read_json(path)

    assert result == {"hello": "world"}


def test_build_account(mock_profile):
    result = PlayStationSnapshotBuilder._build_account(mock_profile)

    assert result.online_id == "TestUser"
    assert result.account_id == "123456789"
    assert result.np_id == "abcdefg1234567"
    assert result.languages == ["en-GB"]
    assert result.avatar_url == "https://test-url.com/test_image.png"


def test_build_account_without_avatar(mock_profile):
    mock_profile["profile"]["avatarUrls"] = []

    result = PlayStationSnapshotBuilder._build_account(mock_profile)

    assert result.avatar_url is None


def test_build_account_without_optional_fields(mock_profile):
    del mock_profile["profile"]["npId"]
    del mock_profile["profile"]["languagesUsed"]
    del mock_profile["profile"]["avatarUrls"]

    result = PlayStationSnapshotBuilder._build_account(mock_profile)

    assert result.np_id is None
    assert result.languages == []
    assert result.avatar_url is None


def test_build_trophy_summary(mock_profile):
    result = PlayStationSnapshotBuilder._build_trophy_summary(mock_profile)

    assert result.level == 250
    assert result.level_progress == 50

    assert result.earned.bronze == 864
    assert result.earned.silver == 192
    assert result.earned.gold == 21
    assert result.earned.platinum == 1


def test_build_devices_groups_activations_by_device(mock_devices):
    result = PlayStationSnapshotBuilder._build_devices(mock_devices)

    assert len(result) == 3

    ps3 = next(
        device
        for device in result
        if device.device_id == "asd156a1da61da3d24aw8c1a132da0w5d4a3"
    )

    assert ps3.device_name == "My Test PS3 System"
    assert ps3.device_type == "PS3"
    assert ps3.account_device_vector is None

    assert len(ps3.activations) == 1

    assert ps3.activations[0].activation_type == "PSN"


def test_build_devices_converts_activation_date_to_datetime(
    mock_devices,
):
    result = PlayStationSnapshotBuilder._build_devices(mock_devices)

    activation = result[0].activations[0]

    assert activation.activation_date.year == 2015
    assert activation.activation_date.month == 2
    assert activation.activation_date.day == 28
    assert activation.activation_date.tzinfo == UTC


@pytest.mark.parametrize(
    (
        "title",
        "expected_content_type",
        "expected_classification_source",
    ),
    [
        (
            {
                "name": "Test PS5 Game",
                "category": "ps5_native_game",
            },
            "game",
            "playstation_category",
        ),
        (
            {
                "name": "Test PS4 Game",
                "category": "ps4_game",
            },
            "game",
            "playstation_category",
        ),
        (
            {
                "name": "Spotify",
                "category": "unknown",
            },
            "application",
            "known_application",
        ),
        (
            {
                "name": "Mystery Game",
                "category": "unknown",
            },
            "game",
            "unknown_category_assumed_game",
        ),
    ],
)
def test_classify_title(
    title,
    expected_content_type,
    expected_classification_source,
):
    result = PlayStationSnapshotBuilder._classify_title(title)

    assert result == (
        expected_content_type,
        expected_classification_source,
    )


def test_build_played_titles(
    snapshot_builder,
    mock_played_titles,
):
    result = snapshot_builder._build_played_titles(mock_played_titles)

    assert len(result) == 3

    game = result[0]

    assert game.title_id == "TEST12345_00"
    assert game.name == "Test Game"
    assert game.reported_category == "unknown"
    assert game.content_type == "game"
    assert game.classification_source == "unknown_category_assumed_game"
    assert game.play_count == 154
    assert game.play_duration_seconds == 62856


def test_build_played_titles_classifies_playstation_game(
    snapshot_builder,
    mock_played_titles,
):
    result = snapshot_builder._build_played_titles(mock_played_titles)

    game = result[1]

    assert game.name == "Test Game 2"
    assert game.content_type == "game"
    assert game.classification_source == "playstation_category"


def test_build_played_titles_classifies_known_application(
    snapshot_builder,
    mock_played_titles,
):
    spotify = mock_played_titles[0].copy()
    spotify["name"] = "Spotify"
    spotify["category"] = "unknown"

    result = snapshot_builder._build_played_titles([spotify])

    assert result[0].content_type == "application"
    assert result[0].classification_source == "known_application"


def test_build_played_titles_assumes_unknown_title_is_game(
    snapshot_builder,
    mock_played_titles,
):
    result = snapshot_builder._build_played_titles(mock_played_titles)

    mystery_game = result[0]

    assert mystery_game.content_type == "game"
    assert mystery_game.classification_source == "unknown_category_assumed_game"


def test_convert_trophy_counts():
    counts = {
        "bronze": 10,
        "silver": 5,
        "gold": 2,
        "platinum": 1,
    }

    result = PlayStationSnapshotBuilder._convert_trophy_counts(counts)

    assert result.bronze == 10
    assert result.silver == 5
    assert result.gold == 2
    assert result.platinum == 1


@pytest.mark.parametrize(
    ("rarity_value", "expected"),
    [
        (0, "ultra_rare"),
        (1, "very_rare"),
        (2, "rare"),
        (3, "common"),
    ],
)
def test_build_trophy_maps_rarity(
    mock_collected_trophies,
    rarity_value,
    expected,
):
    trophy = mock_collected_trophies[0].copy()
    trophy["trophy_rarity"] = rarity_value

    result = PlayStationSnapshotBuilder._build_trophy(trophy)

    assert result.rarity == expected


def test_build_trophy_handles_missing_rarity(
    mock_collected_trophies,
):
    trophy = mock_collected_trophies[0].copy()
    trophy.pop("trophy_rarity")

    result = PlayStationSnapshotBuilder._build_trophy(trophy)

    assert result.rarity is None


def test_build_trophy_converts_earn_rate_to_float(
    mock_collected_trophies,
):
    result = PlayStationSnapshotBuilder._build_trophy(mock_collected_trophies[0])

    assert result.earn_rate == 77.6
    assert isinstance(result.earn_rate, float)


def test_build_trophy_handles_missing_earn_rate(
    mock_collected_trophies,
):
    trophy = mock_collected_trophies[0].copy()
    trophy.pop("trophy_earn_rate")

    result = PlayStationSnapshotBuilder._build_trophy(trophy)

    assert result.earn_rate is None


def test_build_trophy_maps_user_progress(
    mock_collected_trophies,
):
    trophy = mock_collected_trophies[0].copy()

    trophy["earned"] = True
    trophy["earned_date_time"] = "2026-01-01T12:00:00+00:00"
    trophy["progress"] = 50
    trophy["progress_rate"] = 50
    trophy["progressed_date_time"] = "2026-01-01T12:00:00+00:00"

    result = PlayStationSnapshotBuilder._build_trophy(trophy)

    assert result.user_progress.earned is True
    assert result.user_progress.progress == 50
    assert result.user_progress.progress_rate == 50


def test_build_trophy_groups_groups_trophies_by_group(
    snapshot_builder,
    mock_collected_trophies,
):
    trophies = [trophy.copy() for trophy in mock_collected_trophies]

    trophies[0]["trophy_group_id"] = "default"
    trophies[1]["trophy_group_id"] = "dlc-1"

    result = snapshot_builder._build_trophy_groups(trophies)

    assert len(result) == 2

    default_group = next(group for group in result if group.group_id == "default")

    dlc_group = next(group for group in result if group.group_id == "dlc-1")

    assert len(default_group.trophies) == 1
    assert len(dlc_group.trophies) == 1

    assert default_group.trophies[0].name == "Test Trophy 1"
    assert dlc_group.trophies[0].name == "Test Trophy 2"


def test_build_trophy_titles_reads_cached_trophies(
    snapshot_builder,
    mock_trophy_titles,
):
    result = snapshot_builder._build_trophy_titles(mock_trophy_titles)

    assert len(result) == 1

    title = result[0]

    assert title.np_communication_id == "TEST12345_00"
    assert title.title_name == "Test Game"
    assert title.platforms == ["PS5"]
    assert title.progress == 21

    assert title.earned_trophies.bronze == 28
    assert title.earned_trophies.silver == 8
    assert title.earned_trophies.gold == 1
    assert title.earned_trophies.platinum == 0

    assert title.defined_trophies.platinum == 1

    assert len(title.groups) == 1
    assert len(title.groups[0].trophies) == 2


def test_build_trophy_titles_uses_empty_groups_when_cache_missing(
    snapshot_builder,
    mock_trophy_titles,
):
    communication_id = mock_trophy_titles[0]["np_communication_id"]

    trophy_path = snapshot_builder.trophy_dir / f"{communication_id}.json"

    trophy_path.unlink()

    result = snapshot_builder._build_trophy_titles(mock_trophy_titles)

    assert len(result) == 1
    assert result[0].groups == []


def test_build_trophy_title_defaults_nullable_booleans_to_false(
    snapshot_builder,
    mock_trophy_titles,
):
    mock_trophy_titles[0]["has_trophy_groups"] = None
    mock_trophy_titles[0]["hidden_flag"] = None

    result = snapshot_builder._build_trophy_titles(mock_trophy_titles)

    assert result[0].has_trophy_groups is False
    assert result[0].hidden is False


def test_count_cached_trophy_titles(
    snapshot_builder,
    mock_trophy_titles,
):
    result = snapshot_builder._count_cached_trophy_titles(mock_trophy_titles)

    assert result == 1


def test_count_cached_trophy_titles_returns_zero_when_missing(
    snapshot_builder,
    mock_trophy_titles,
):
    communication_id = mock_trophy_titles[0]["np_communication_id"]

    trophy_path = snapshot_builder.trophy_dir / f"{communication_id}.json"

    trophy_path.unlink()

    result = snapshot_builder._count_cached_trophy_titles(mock_trophy_titles)

    assert result == 0


def test_build_validation_when_import_is_complete(
    snapshot_builder,
    snapshot_profile,
    mock_trophy_titles,
):
    trophy_summary = snapshot_builder._build_trophy_summary(snapshot_profile)

    trophy_titles = snapshot_builder._build_trophy_titles(mock_trophy_titles)

    result = snapshot_builder._build_validation(
        trophy_summary=trophy_summary,
        trophy_titles=trophy_titles,
        expected_trophy_titles_count=1,
        imported_trophy_detail_sets_count=1,
    )

    assert result.trophy_title_summary_complete is True
    assert result.trophy_detail_import_complete is True

    assert result.expected_trophy_titles_count == 1
    assert result.imported_trophy_titles_count == 1

    assert result.expected_trophy_detail_sets_count == 1
    assert result.imported_trophy_detail_sets_count == 1

    assert result.trophy_totals_match is True
    assert result.warnings == []


def test_build_validation_warns_when_trophy_titles_are_missing(
    snapshot_builder,
    mock_profile,
):
    trophy_summary = snapshot_builder._build_trophy_summary(mock_profile)

    result = snapshot_builder._build_validation(
        trophy_summary=trophy_summary,
        trophy_titles=[],
        expected_trophy_titles_count=1,
        imported_trophy_detail_sets_count=0,
    )

    assert result.trophy_title_summary_complete is False
    assert result.trophy_detail_import_complete is False

    assert "Trophy title summary import is incomplete" in result.warnings[0]

    assert "Detailed trophy import is incomplete" in result.warnings[1]


def test_build_validation_warns_when_trophy_totals_do_not_match(
    snapshot_builder,
    snapshot_profile,
    mock_trophy_titles,
):
    snapshot_profile["profile"]["trophySummary"]["earnedTrophies"]["bronze"] = 50

    trophy_summary = snapshot_builder._build_trophy_summary(snapshot_profile)

    trophy_titles = snapshot_builder._build_trophy_titles(mock_trophy_titles)

    result = snapshot_builder._build_validation(
        trophy_summary=trophy_summary,
        trophy_titles=trophy_titles,
        expected_trophy_titles_count=1,
        imported_trophy_detail_sets_count=1,
    )

    assert result.trophy_title_summary_complete is True
    assert result.trophy_totals_match is False

    assert (
        "Imported trophy summary totals do not match "
        "the PlayStation profile totals." in result.warnings
    )


def test_build_returns_complete_snapshot(snapshot_builder):
    result = snapshot_builder.build()

    assert result.account.online_id == "TestUser"
    assert result.account.account_id == "123456789"

    assert result.trophy_summary.level == 250

    assert len(result.devices) == 3
    assert len(result.played_titles) == 3
    assert len(result.trophy_titles) == 1

    assert result.validation.trophy_title_summary_complete is True
    assert result.validation.trophy_detail_import_complete is True
    assert result.validation.trophy_totals_match is True

    assert result.snapshot.generated_at.tzinfo == UTC


def test_validate_returns_validation_result(snapshot_builder):
    result = snapshot_builder.validate()

    assert result.trophy_title_summary_complete is True
    assert result.trophy_detail_import_complete is True
    assert result.trophy_totals_match is True
    assert result.warnings == []
