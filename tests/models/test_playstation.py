import pytest
from pydantic import ValidationError

from game_vault.models.playstation import (
    PlayStationSourceKey,
    PlayStationTitleCandidate,
    PlaystationTrophyGroup,
    PlaystationTrophyTitle,
    TrophyCounts,
)


def test_candidate_validates_nested_source_keys_and_round_trips():
    candidate = PlayStationTitleCandidate.model_validate(
        {
            "source_key": [{"source_type": "Played Title", "source_id": "PPSA001"}],
            "names": ["Test Game"],
            "platforms": ["PS5"],
            "product_ids": ["PPSA001"],
            "np_communication_ids": [],
            "np_title_ids": [],
        }
    )
    assert candidate.source_key == [
        PlayStationSourceKey(source_type="Played Title", source_id="PPSA001")
    ]
    assert candidate.platforms[0].value == "PS5"
    assert candidate.played_title is None
    assert candidate.trophy_title is None
    assert (
        PlayStationTitleCandidate.model_validate_json(candidate.model_dump_json())
        == candidate
    )


def test_candidate_rejects_unknown_platform():
    with pytest.raises(ValidationError, match="platforms"):
        PlayStationTitleCandidate(
            source_key=[],
            names=[],
            platforms=["PS6"],
            product_ids=[],
            np_communication_ids=[],
            np_title_ids=[],
        )


def test_trophy_counts_total_sums_all_trophy_types():
    counts = TrophyCounts(
        bronze=4,
        silver=3,
        gold=2,
        platinum=1,
    )

    assert counts.total == 10


def test_trophy_title_rejects_none_for_boolean_fields():
    with pytest.raises(ValidationError):
        PlaystationTrophyTitle.model_validate(
            {
                "np_communication_id": "TEST12345_00",
                "np_service_name": "trophy2",
                "np_title_id": None,
                "trophy_set_version": "01.00",
                "title_name": "Test Game",
                "title_detail": None,
                "title_icon_url": None,
                "platforms": ["PS5"],
                "has_trophy_groups": None,
                "hidden": None,
                "progress": 0,
                "earned_trophies": {
                    "bronze": 0,
                    "silver": 0,
                    "gold": 0,
                    "platinum": 0,
                },
                "defined_trophies": {
                    "bronze": 1,
                    "silver": 0,
                    "gold": 0,
                    "platinum": 0,
                },
                "last_updated_at": None,
                "groups": [],
            }
        )


def test_trophy_group_defaults_to_empty_trophies():
    group = PlaystationTrophyGroup(
        group_id="default",
    )

    assert group.trophies == []


# def test_trophy_groups_do_not_share_trophy_lists():
#     first = PlaystationTrophyGroup(group_id="default")
#     second = PlaystationTrophyGroup(group_id="dlc-1")
#
#     first.trophies.append(...)
#
#     assert second.trophies == []
