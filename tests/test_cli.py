import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from game_vault import cli


def test_main_dispatches_psn_command(monkeypatch):
    handle_psn_command = Mock()
    monkeypatch.setattr(cli, "handle_psn_command", handle_psn_command)
    monkeypatch.setattr(sys, "argv", ["game-vault", "psn", "collect"])

    cli.main()

    handle_psn_command.assert_called_once_with("collect")


@pytest.mark.parametrize(
    ("command", "expected_calls"),
    [
        ("collect", ["collect"]),
        ("build", ["build"]),
        ("sync", ["collect", "build"]),
        ("validate", ["validate"]),
        ("map", ["map"]),
    ],
)
def test_handle_psn_command_dispatches_expected_action(
    monkeypatch,
    command,
    expected_calls,
):
    actions = {
        "collect": Mock(),
        "build": Mock(),
        "validate": Mock(),
        "map": Mock(),
    }
    monkeypatch.setattr(cli, "collect_playstation_data", actions["collect"])
    monkeypatch.setattr(cli, "build_playstation_snapshot", actions["build"])
    monkeypatch.setattr(cli, "validate_playstation_snapshot", actions["validate"])
    monkeypatch.setattr(cli, "map_playstation_snapshot", actions["map"])

    cli.handle_psn_command(command)

    for action_name, action in actions.items():
        assert action.call_count == expected_calls.count(action_name)


def test_collect_playstation_data_builds_collector_and_collects(monkeypatch):
    client = Mock()
    create_psn_client = Mock(return_value=client)
    client_module = ModuleType("game_vault.playstation_client")
    client_module.create_psn_client = create_psn_client
    monkeypatch.setitem(
        sys.modules,
        "game_vault.playstation_client",
        client_module,
    )

    from game_vault.collectors import playstation_collector

    collector = Mock()
    collector_class = Mock(return_value=collector)
    monkeypatch.setattr(
        playstation_collector,
        "PlayStationCollector",
        collector_class,
    )

    cli.collect_playstation_data()

    create_psn_client.assert_called_once_with()
    collector_class.assert_called_once_with(client)
    collector.collect_all.assert_called_once_with()


def test_build_playstation_snapshot_writes_snapshot(
    monkeypatch,
    tmp_path,
    capsys,
):
    from game_vault.services import playstation_snapshot_builder

    snapshot = Mock()
    snapshot.model_dump_json.return_value = '{"source": "playstation"}'
    builder = Mock()
    builder.build.return_value = snapshot
    builder_class = Mock(return_value=builder)
    monkeypatch.setattr(
        playstation_snapshot_builder,
        "PlayStationSnapshotBuilder",
        builder_class,
    )
    monkeypatch.chdir(tmp_path)

    cli.build_playstation_snapshot()

    output_path = tmp_path / "data/playstation/snapshot.json"
    assert output_path.read_text(encoding="utf-8") == '{"source": "playstation"}'
    builder_class.assert_called_once_with()
    builder.build.assert_called_once_with()
    snapshot.model_dump_json.assert_called_once_with(indent=4)
    assert capsys.readouterr().out == (
        "Snapshot written to data/playstation/snapshot.json\n"
    )


def test_validate_playstation_snapshot_prints_validation_result(
    monkeypatch,
    capsys,
):
    from game_vault.services import playstation_snapshot_builder

    validation = Mock(
        imported_trophy_titles_count=2,
        expected_trophy_titles_count=3,
        imported_trophy_detail_sets_count=4,
        expected_trophy_detail_sets_count=5,
        trophy_totals_match=False,
        warnings=["missing trophy details"],
    )
    builder = Mock()
    builder.validate.return_value = validation
    monkeypatch.setattr(
        playstation_snapshot_builder,
        "PlayStationSnapshotBuilder",
        Mock(return_value=builder),
    )

    cli.validate_playstation_snapshot()

    assert capsys.readouterr().out.splitlines() == [
        "Trophy titles imported: 2/3",
        "Trophy details imported: 4/5",
        "Trophy totals match? False",
        "Warnings: ['missing trophy details']",
    ]
