import json
from datetime import datetime, timedelta
from enum import Enum
from unittest.mock import Mock, call, patch

import pytest


@pytest.mark.parametrize(
    (
        "client_method",
        "return_value_fixture",
        "collector_method",
        "output_filename",
    ),
    [
        (
            "get_profile_legacy",
            "mock_profile",
            "collect_profile",
            "profile.json",
        ),
        (
            "get_account_devices",
            "mock_devices",
            "collect_devices",
            "devices.json",
        ),
        (
            "title_stats",
            "mock_played_titles",
            "collect_played_titles",
            "played_titles.json",
        ),
        (
            "trophy_titles",
            "mock_trophy_titles",
            "collect_trophy_titles",
            "trophy_titles.json",
        ),
    ],
)
def test_collector_writes_responses_to_json(
    request,
    mock_playstation_collector,
    mock_psn_client,
    tmp_path,
    client_method,
    return_value_fixture,
    collector_method,
    output_filename,
):
    expected_data = request.getfixturevalue(return_value_fixture)

    mocked_method = getattr(mock_psn_client, client_method)
    mocked_method.return_value = expected_data

    method_under_test = getattr(mock_playstation_collector, collector_method)
    method_under_test()

    output_file = tmp_path / output_filename

    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert data == expected_data

    mocked_method.assert_called_once()


def test_collect_trophies_for_title(
    mock_playstation_collector,
    mock_psn_client,
    mock_trophy_title,
    mock_collected_trophies,
):
    mock_psn_client.trophies.return_value = mock_collected_trophies

    mock_playstation_collector.collect_trophies_for_title(mock_trophy_title)

    output_file = (
        mock_playstation_collector.trophy_dir
        / f"{mock_trophy_title.np_communication_id}.json"
    )

    assert output_file.exists()

    with output_file.open() as file:
        result = json.load(file)

    assert result == mock_collected_trophies

    mock_psn_client.trophies.assert_called_once_with(
        np_communication_id="TEST12345_00",
        platform="PS5",
        include_progress=True,
        trophy_group_id="all",
    )


def test_collect_trophies_for_title_skips_cached_file(
    mock_playstation_collector,
    mock_psn_client,
    mock_trophy_title,
):
    output_file = (
        mock_playstation_collector.trophy_dir
        / f"{mock_trophy_title.np_communication_id}.json"
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('{"cached": true}')

    mock_playstation_collector.collect_trophies_for_title(mock_trophy_title)

    mock_psn_client.trophies.assert_not_called()

    assert json.loads(output_file.read_text()) == {"cached": True}


def test_collect_trophies_for_title_force_overwrites_cache(
    mock_playstation_collector,
    mock_psn_client,
    mock_trophy_title,
    mock_collected_trophies,
):
    output_file = (
        mock_playstation_collector.trophy_dir
        / f"{mock_trophy_title.np_communication_id}.json"
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('{"cached": true}')

    mock_psn_client.trophies.return_value = mock_collected_trophies

    mock_playstation_collector.collect_trophies_for_title(
        mock_trophy_title,
        force=True,
    )

    mock_psn_client.trophies.assert_called_once()

    with output_file.open() as file:
        result = json.load(file)

    assert result == mock_collected_trophies


def test_collect_all_trophies(
    mock_playstation_collector,
):
    trophy_title_1 = Mock()
    trophy_title_1.title_name = "Test Game 1"

    trophy_title_2 = Mock()
    trophy_title_2.title_name = "Test Game 2"

    trophy_titles = [
        trophy_title_1,
        trophy_title_2,
    ]

    mock_playstation_collector.collect_trophies_for_title = Mock()

    with patch("time.sleep"):
        mock_playstation_collector.collect_all_trophies(
            trophy_titles,
            force=True,
        )

    assert mock_playstation_collector.collect_trophies_for_title.call_args_list == [
        call(trophy_title_1, force=True),
        call(trophy_title_2, force=True),
    ]


def test_collect_all_trophies_continues_after_failure(mock_playstation_collector):
    trophy_title_1 = Mock()
    trophy_title_1.title_name = "Broken Game"

    trophy_title_2 = Mock()
    trophy_title_2.title_name = "Working Game"

    trophy_titles = [
        trophy_title_1,
        trophy_title_2,
    ]

    mock_playstation_collector.collect_trophies_for_title = Mock(
        side_effect=[
            Exception("API failure"),
            None,
        ]
    )

    with patch("time.sleep"):
        mock_playstation_collector.collect_all_trophies(trophy_titles)

    assert mock_playstation_collector.collect_trophies_for_title.call_args_list == [
        call(trophy_title_1, force=False),
        call(trophy_title_2, force=False),
    ]


@patch("time.sleep")
def test_collect_all_trophies_sleeps_after_success(
    mock_sleep,
    mock_playstation_collector,
):
    trophy_title = Mock()
    trophy_title.title_name = "Test Game"

    mock_playstation_collector.collect_trophies_for_title = Mock()

    mock_playstation_collector.collect_all_trophies([trophy_title])

    mock_sleep.assert_called_once_with(0.5)


def test_collect_all(mock_playstation_collector):
    trophy_titles = [
        Mock(),
        Mock(),
    ]

    mock_playstation_collector.collect_profile = Mock()
    mock_playstation_collector.collect_devices = Mock()
    mock_playstation_collector.collect_played_titles = Mock()

    mock_playstation_collector.collect_trophy_titles = Mock(return_value=trophy_titles)

    mock_playstation_collector.collect_all_trophies = Mock()

    mock_playstation_collector.collect_all()

    mock_playstation_collector.collect_profile.assert_called_once_with()
    mock_playstation_collector.collect_devices.assert_called_once_with()
    mock_playstation_collector.collect_played_titles.assert_called_once_with()
    mock_playstation_collector.collect_trophy_titles.assert_called_once_with()

    mock_playstation_collector.collect_all_trophies.assert_called_once_with(
        trophy_titles
    )


class ExampleEnum(Enum):
    VALUE = "value"


class ExampleObject:
    def __init__(self):
        self.name = "Minecraft"
        self.hours = timedelta(hours=2)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            datetime(2026, 8, 30, 20, 15, 30),
            "2026-08-30T20:15:30",
        ),
        (
            timedelta(hours=2, minutes=30),
            9000,
        ),
        (
            ExampleEnum.VALUE,
            "value",
        ),
        (
            ["Minecraft", timedelta(minutes=5)],
            ["Minecraft", 300],
        ),
        (
            ("Minecraft", timedelta(minutes=5)),
            ["Minecraft", 300],
        ),
        (
            {
                "game": "Minecraft",
                "playtime": timedelta(hours=1),
            },
            {
                "game": "Minecraft",
                "playtime": 3600,
            },
        ),
        (
            "Minecraft",
            "Minecraft",
        ),
        (
            123,
            123,
        ),
        (
            None,
            None,
        ),
    ],
)
def test_to_jsonable(mock_playstation_collector, value, expected):
    assert mock_playstation_collector.to_jsonable(value) == expected


def test_to_jsonable_converts_frozenset(mock_playstation_collector):
    value = frozenset(["Minecraft", "The Witcher 3"])

    result = mock_playstation_collector.to_jsonable(value)

    assert sorted(result) == ["Minecraft", "The Witcher 3"]


def test_to_jsonable_converts_object_with_dict(mock_playstation_collector):
    value = ExampleObject()

    result = mock_playstation_collector.to_jsonable(value)

    assert result == {
        "name": "Minecraft",
        "hours": 7200,
    }
