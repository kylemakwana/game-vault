import pytest

from game_vault.config import IdentifierTypeEnum, PlayStationPlatformEnum
from game_vault.services.playstation_discovery_service import (
    PlayStationDiscoveryService,
)


@pytest.fixture
def snapshot(snapshot_builder):
    snapshot = snapshot_builder.build()
    snapshot.played_titles = snapshot.played_titles[:1]
    snapshot.played_titles[0].reported_category = "ps5_native_game"
    return snapshot


def test_empty_snapshot(snapshot):
    snapshot.played_titles = []
    snapshot.trophy_titles = []
    assert PlayStationDiscoveryService().discover(snapshot) == []


@pytest.mark.parametrize("np_title_id", [None, "PPSA00001_00"])
@pytest.mark.parametrize("name", ["Test Game", "  TEST\tGame\u2122\u00ae  "])
def test_matching_titles_merge_evidence_without_changing_snapshot(
    snapshot, name, np_title_id
):
    snapshot.trophy_titles[0].title_name = name
    snapshot.trophy_titles[0].np_title_id = np_title_id
    snapshot.trophy_titles[0].platforms = ["PS5", "PS4", "PS4"]
    before = snapshot.model_dump()

    service = PlayStationDiscoveryService()
    (candidate,) = service.discover(snapshot)

    assert candidate.names == (
        ["Test Game"] if name == "Test Game" else ["Test Game", name]
    )
    assert candidate.platforms == [
        PlayStationPlatformEnum.PS5,
        PlayStationPlatformEnum.PS4,
    ]
    assert candidate.title_ids == ["TEST12345_00"]
    assert candidate.np_communication_ids == ["TEST12345_00"]
    assert candidate.np_title_ids == ([] if np_title_id is None else [np_title_id])
    assert [(key.source_type, key.source_id) for key in candidate.source_key] == [
        (IdentifierTypeEnum.PLAYED_TITLE, "TEST12345_00"),
        (IdentifierTypeEnum.TROPHY_TITLE, "TEST12345_00"),
    ]
    assert candidate.played_title == snapshot.played_titles[0]
    assert candidate.trophy_title == snapshot.trophy_titles[0]
    assert snapshot.model_dump() == before
    assert service.discover(snapshot) == [candidate]


@pytest.mark.parametrize(
    ("category", "name", "platforms"),
    [
        ("ps4_game", "Test Game", ["PS5"]),
        ("ps5_native_game", "Different Game", ["PS5"]),
        ("unknown", "Test Game", ["PS5"]),
        ("ps5_native_game", "Test Game", []),
    ],
)
def test_nonmatching_titles_remain_separate(snapshot, category, name, platforms):
    snapshot.played_titles[0].reported_category = category
    snapshot.trophy_titles[0].title_name = name
    snapshot.trophy_titles[0].platforms = platforms
    played, trophy = PlayStationDiscoveryService().discover(snapshot)
    assert played.trophy_title is None
    assert trophy.played_title is None
    assert played.names == ["Test Game"]
    assert trophy.names == [name]


@pytest.mark.parametrize("np_title_id", [None, "NP00001"])
def test_trophy_only_deduplicates_platforms(snapshot, np_title_id):
    snapshot.played_titles = []
    snapshot.trophy_titles[0].platforms = ["ps3", "PS3", "ps4", "PS5", "Vita"]
    snapshot.trophy_titles[0].np_title_id = np_title_id
    (candidate,) = PlayStationDiscoveryService().discover(snapshot)
    assert candidate.platforms == [
        PlayStationPlatformEnum.PS3,
        PlayStationPlatformEnum.PS4,
        PlayStationPlatformEnum.PS5,
        PlayStationPlatformEnum.UNKNOWN,
    ]
    assert candidate.title_ids == []
    assert candidate.np_title_ids == ([] if np_title_id is None else [np_title_id])
    assert candidate.np_communication_ids == ["TEST12345_00"]
    assert candidate.source_key[0].source_type == IdentifierTypeEnum.TROPHY_TITLE


def test_second_trophy_set_does_not_overwrite_first_match(snapshot):
    second = snapshot.trophy_titles[0].model_copy(
        update={"np_communication_id": "SECOND"}, deep=True
    )
    snapshot.trophy_titles.append(second)
    merged, standalone = PlayStationDiscoveryService().discover(snapshot)
    assert merged.np_communication_ids == ["TEST12345_00"]
    assert standalone.np_communication_ids == ["SECOND"]
    assert standalone.played_title is None


def test_duplicate_played_names_match_each_trophy_only_once(snapshot):
    snapshot.played_titles.append(
        snapshot.played_titles[0].model_copy(
            update={"title_id": "SECOND_PRODUCT"}, deep=True
        )
    )
    snapshot.trophy_titles.append(
        snapshot.trophy_titles[0].model_copy(
            update={"np_communication_id": "SECOND_SET"}, deep=True
        )
    )
    first, second = PlayStationDiscoveryService().discover(snapshot)
    assert first.title_ids == ["TEST12345_00"]
    assert first.np_communication_ids == ["TEST12345_00"]
    assert second.title_ids == ["SECOND_PRODUCT"]
    assert second.np_communication_ids == ["SECOND_SET"]


@pytest.mark.parametrize("platform", list(PlayStationPlatformEnum))
def test_platform_enum_is_preserved(platform):
    assert PlayStationDiscoveryService._map_platform(platform) is platform
