import json

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
