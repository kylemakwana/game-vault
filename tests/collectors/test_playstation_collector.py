import json
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
            "legacy_profile",
            "collect_profile",
            "profile.json",
        ),
        (
            "get_account_devices",
            "devices",
            "collect_devices",
            "devices.json",
        ),
        (
            "title_stats",
            "played_titles",
            "collect_played_titles",
            "played_titles.json",
        ),
        (
            "trophy_titles",
            "trophy_titles",
            "collect_trophy_titles",
            "trophy_titles.json",
        ),
    ],
)
def test_collector_writes_responses_to_json(
    request,
    playstation_collector,
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

    method_under_test = getattr(playstation_collector, collector_method)
    method_under_test()

    output_file = tmp_path / output_filename

    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert data == expected_data

    mocked_method.assert_called_once()


def test_collect_trophies_for_title(
    playstation_collector,
    mock_psn_client,
    trophy_title,
    collected_trophies,
):
    mock_psn_client.trophies.return_value = collected_trophies

    playstation_collector.collect_trophies_for_title(trophy_title)

    output_file = (
        playstation_collector.trophy_dir / f"{trophy_title.np_communication_id}.json"
    )

    assert output_file.exists()

    with output_file.open() as file:
        result = json.load(file)

    assert result == collected_trophies

    mock_psn_client.trophies.assert_called_once_with(
        np_communication_id="TEST12345_00",
        platform="PS5",
        include_progress=True,
        trophy_group_id="all",
    )


def test_collect_trophies_for_title_skips_cached_file(
    playstation_collector,
    mock_psn_client,
    trophy_title,
):
    output_file = (
        playstation_collector.trophy_dir / f"{trophy_title.np_communication_id}.json"
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('{"cached": true}')

    playstation_collector.collect_trophies_for_title(trophy_title)

    mock_psn_client.trophies.assert_not_called()

    assert json.loads(output_file.read_text()) == {"cached": True}


def test_collect_trophies_for_title_force_overwrites_cache(
    playstation_collector,
    mock_psn_client,
    trophy_title,
    collected_trophies,
):
    output_file = (
        playstation_collector.trophy_dir / f"{trophy_title.np_communication_id}.json"
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('{"cached": true}')

    mock_psn_client.trophies.return_value = collected_trophies

    playstation_collector.collect_trophies_for_title(
        trophy_title,
        force=True,
    )

    mock_psn_client.trophies.assert_called_once()

    with output_file.open() as file:
        result = json.load(file)

    assert result == collected_trophies


def test_collect_all_trophies(
    playstation_collector,
):
    trophy_title_1 = Mock()
    trophy_title_1.title_name = "Test Game 1"

    trophy_title_2 = Mock()
    trophy_title_2.title_name = "Test Game 2"

    trophy_titles = [
        trophy_title_1,
        trophy_title_2,
    ]

    playstation_collector.collect_trophies_for_title = Mock()

    with patch("time.sleep"):
        playstation_collector.collect_all_trophies(
            trophy_titles,
            force=True,
        )

    assert playstation_collector.collect_trophies_for_title.call_args_list == [
        call(trophy_title_1, force=True),
        call(trophy_title_2, force=True),
    ]


def test_collect_all_trophies_continues_after_failure(playstation_collector):
    trophy_title_1 = Mock()
    trophy_title_1.title_name = "Broken Game"

    trophy_title_2 = Mock()
    trophy_title_2.title_name = "Working Game"

    trophy_titles = [
        trophy_title_1,
        trophy_title_2,
    ]

    playstation_collector.collect_trophies_for_title = Mock(
        side_effect=[
            Exception("API failure"),
            None,
        ]
    )

    with patch("time.sleep"):
        playstation_collector.collect_all_trophies(trophy_titles)

    assert playstation_collector.collect_trophies_for_title.call_args_list == [
        call(trophy_title_1, force=False),
        call(trophy_title_2, force=False),
    ]


@patch("time.sleep")
def test_collect_all_trophies_sleeps_after_success(
    mock_sleep,
    playstation_collector,
):
    trophy_title = Mock()
    trophy_title.title_name = "Test Game"

    playstation_collector.collect_trophies_for_title = Mock()

    playstation_collector.collect_all_trophies([trophy_title])

    mock_sleep.assert_called_once_with(0.5)


def test_collect_all(playstation_collector):
    trophy_titles = [
        Mock(),
        Mock(),
    ]

    playstation_collector.collect_profile = Mock()
    playstation_collector.collect_devices = Mock()
    playstation_collector.collect_played_titles = Mock()

    playstation_collector.collect_trophy_titles = Mock(return_value=trophy_titles)

    playstation_collector.collect_all_trophies = Mock()

    playstation_collector.collect_all()

    playstation_collector.collect_profile.assert_called_once_with()
    playstation_collector.collect_devices.assert_called_once_with()
    playstation_collector.collect_played_titles.assert_called_once_with()
    playstation_collector.collect_trophy_titles.assert_called_once_with()

    playstation_collector.collect_all_trophies.assert_called_once_with(trophy_titles)
