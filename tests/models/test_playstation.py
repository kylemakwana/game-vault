import pytest
from pydantic import ValidationError

from game_vault.models.playstation import PlaystationTrophyGroup, PlaystationTrophyTitle


def test_trophy_title_rejects_none_for_boolean_fields():
    with pytest.raises(ValidationError):
        PlaystationTrophyTitle(
            np_communication_id="TEST12345_00",
            np_service_name="trophy2",
            np_title_id=None,
            trophy_set_version="01.00",
            title_name="Test Game",
            title_detail=None,
            title_icon_url=None,
            platforms=["PS5"],
            has_trophy_groups=None,
            hidden=None,
            progress=0,
            earned_trophies={
                "bronze": 0,
                "silver": 0,
                "gold": 0,
                "platinum": 0,
            },
            defined_trophies={
                "bronze": 1,
                "silver": 0,
                "gold": 0,
                "platinum": 0,
            },
            last_updated_at=None,
            groups=[],
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
