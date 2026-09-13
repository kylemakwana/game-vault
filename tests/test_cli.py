import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, Mock

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
        ("discover", ["discover"]),
        ("import", ["import"]),
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
        "discover": Mock(),
        "import": Mock(),
    }
    monkeypatch.setattr(cli, "collect_playstation_data", actions["collect"])
    monkeypatch.setattr(cli, "build_playstation_snapshot", actions["build"])
    monkeypatch.setattr(cli, "validate_playstation_snapshot", actions["validate"])
    monkeypatch.setattr(cli, "map_playstation_snapshot", actions["map"])
    monkeypatch.setattr(cli, "discover_playstation_snapshot", actions["discover"])
    monkeypatch.setattr(cli, "import_playstation", actions["import"])

    cli.handle_psn_command(command)

    for action_name, action in actions.items():
        assert action.call_count == expected_calls.count(action_name)


def test_collect_playstation_data_builds_collector_and_collects(monkeypatch):
    client = Mock()
    create_psn_client = Mock(return_value=client)
    client_module = ModuleType("game_vault.playstation_client")
    setattr(client_module, "create_psn_client", create_psn_client)
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


@pytest.mark.parametrize("build_snapshot", [True, False])
@pytest.mark.parametrize("empty", [True, False])
def test_discovery_writes_results_and_prints_summary(
    monkeypatch,
    tmp_path,
    capsys,
    build_snapshot,
    empty,
):
    from game_vault.models.playstation import PlayStationTitleCandidate
    from game_vault.models.resolution import ResolutionResult

    candidates = (
        []
        if empty
        else [
            PlayStationTitleCandidate.model_validate(
                {
                    "source_key": [],
                    "names": [name],
                    "platforms": ["PS5"],
                    "title_ids": [],
                    "np_communication_ids": [],
                    "np_title_ids": [],
                }
            )
            for name in ("Matched Game", "Unmatched Game", "Ambiguous Game")
        ]
    )
    results = (
        []
        if empty
        else [
            ResolutionResult.model_validate(
                {
                    "status": "matched",
                    "game_release_id": "game-ps5",
                    "match_method": "source_mapping",
                    "confidence": 1.0,
                }
            ),
            ResolutionResult.model_validate({"status": "unmatched"}),
            ResolutionResult.model_validate(
                {
                    "status": "ambiguous",
                    "candidate_release_ids": ["a", "b"],
                }
            ),
        ]
    )
    snapshot = Mock()
    builder = Mock()
    builder.build.return_value = snapshot
    builder_class = Mock(return_value=builder)
    discovery = Mock()
    discovery.discover.return_value = candidates
    resolver = Mock()
    resolver.resolve.side_effect = results
    monkeypatch.setattr(cli, "PlayStationSnapshotBuilder", builder_class)
    monkeypatch.setattr(
        cli, "PlayStationDiscoveryService", Mock(return_value=discovery)
    )
    monkeypatch.setattr(cli, "GameResolutionService", Mock(return_value=resolver))
    monkeypatch.setattr(cli, "get_connection", MagicMock())
    monkeypatch.chdir(tmp_path)

    cli.discover_playstation_snapshot(None if build_snapshot else snapshot)

    assert builder.build.call_count == int(build_snapshot)
    discovery.discover.assert_called_once_with(snapshot)
    assert resolver.resolve.call_count == len(candidates)
    folder = tmp_path / "data/playstation"
    assert json.loads((folder / "candidate_ps_titles.json").read_text()) == [
        candidate.model_dump(mode="json") for candidate in candidates
    ]
    saved = json.loads((folder / "resolution_results.json").read_text())
    assert [item["resolution"] for item in saved] == [
        result.model_dump(mode="json") for result in results
    ]
    assert [item["names"] for item in saved] == [
        candidate.names for candidate in candidates
    ]
    output = capsys.readouterr().out
    assert f"Candidates: {len(candidates)}" in output
    if not empty:
        assert "UNMATCHED: ['Unmatched Game']" in output
        assert "['Matched Game'] -> game-ps5" in output
        assert "ambiguous: 1" in output
        assert "source_mapping: 1" in output


@pytest.mark.parametrize("build_snapshot", [True, False])
def test_map_loads_checked_in_catalogue(monkeypatch, build_snapshot):
    from game_vault.config import SourceTypeMappingEnum
    from game_vault.mappers import playstation_mapper
    from game_vault.services import playstation_snapshot_builder

    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    snapshot = Mock()
    builder = Mock()
    builder.build.return_value = snapshot
    monkeypatch.setattr(
        playstation_snapshot_builder,
        "PlayStationSnapshotBuilder",
        Mock(return_value=builder),
    )
    mapper = Mock()
    mapper_class = Mock(return_value=mapper)
    monkeypatch.setattr(playstation_mapper, "PlayStationMapper", mapper_class)

    assert (
        cli.map_playstation_snapshot(None if build_snapshot else snapshot)
        is mapper.map.return_value
    )
    inputs = mapper_class.call_args.kwargs
    assert inputs["snapshot"] is snapshot
    assert inputs["mappings"]
    releases = {release.id for release in inputs["releases"]}
    for mapping in inputs["mappings"]:
        assert mapping.game_release_id in releases
        assert mapping.source in {item.value for item in SourceTypeMappingEnum}
    assert builder.build.call_count == int(build_snapshot)
    mapper.map.assert_called_once_with()
