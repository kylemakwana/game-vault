import argparse
from pathlib import Path
from pprint import pprint

from game_vault.loaders.catalog_loader import load_catalog
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.series import GameSeries, GameSeriesMembership


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="game-vault",
        description="Game Vault CLI",
    )

    subparsers = parser.add_subparsers(
        dest="platform",
        required=True,
    )

    psn_parser = subparsers.add_parser(
        "psn",
        help="PlayStation commands",
    )

    psn_subparsers = psn_parser.add_subparsers(
        dest="command",
        required=True,
    )

    psn_subparsers.add_parser(
        "collect",
        help="Collect and cache PlayStation data",
    )

    psn_subparsers.add_parser(
        "build",
        help="Build a PlayStation snapshot from cached data",
    )

    psn_subparsers.add_parser(
        "sync",
        help="Collect data and rebuild the snapshot",
    )

    psn_subparsers.add_parser(
        "validate",
        help="Validate the cached PlayStation snapshot",
    )

    psn_subparsers.add_parser(
        "map",
        help="Map the cached PlayStation snapshot to Game Vault format",
    )

    args = parser.parse_args()

    if args.platform == "psn":
        handle_psn_command(args.command)


def handle_psn_command(command: str) -> None:
    if command == "collect":
        collect_playstation_data()

    elif command == "build":
        build_playstation_snapshot()

    elif command == "sync":
        collect_playstation_data()
        build_playstation_snapshot()

    elif command == "validate":
        validate_playstation_snapshot()

    elif command == "map":
        map_playstation_snapshot()


def collect_playstation_data() -> None:
    from game_vault.collectors.playstation_collector import (
        PlayStationCollector,
    )
    from game_vault.psn import create_psn_client

    client = create_psn_client()

    collector = PlayStationCollector(client)
    collector.collect_all()


def build_playstation_snapshot() -> None:
    from pathlib import Path

    from game_vault.services.playstation_snapshot_builder import (
        PlayStationSnapshotBuilder,
    )

    builder = PlayStationSnapshotBuilder()
    snapshot = builder.build()
    output_path = Path("data/playstation/snapshot.json")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        snapshot.model_dump_json(indent=4),
        encoding="utf-8",
    )

    print(f"Snapshot written to {output_path}")


def validate_playstation_snapshot() -> None:
    from game_vault.services.playstation_snapshot_builder import (
        PlayStationSnapshotBuilder,
    )

    builder = PlayStationSnapshotBuilder()
    validation = builder.validate()

    print(
        f"Trophy titles imported: {validation.imported_trophy_titles_count}/"
        f"{validation.expected_trophy_titles_count}"
    )
    print(
        f"Trophy details imported: "
        f"{validation.imported_trophy_detail_sets_count}/"
        f"{validation.expected_trophy_detail_sets_count}"
    )
    print(f"Trophy totals match? {validation.trophy_totals_match}")
    print(f"Warnings: {validation.warnings}")


def map_playstation_snapshot() -> None:
    from game_vault.mappers.playstation_mapper import (
        PlaystationMapper,
    )
    from game_vault.services.playstation_snapshot_builder import (
        PlayStationSnapshotBuilder,
    )

    mappings = load_catalog(
        Path("resources/mappings/playstation.json"), SourceGameMapping
    )
    games = load_catalog(Path("resources/catalog/games.json"), Game)
    releases = load_catalog(Path("resources/catalog/releases.json"), GameRelease)
    series = load_catalog(Path("resources/catalog/series.json"), GameSeries)
    series_memberships = load_catalog(
        Path("resources/catalog/series_memberships.json"), GameSeriesMembership
    )

    builder = PlayStationSnapshotBuilder()
    snapshot = builder.build()

    mapper = PlaystationMapper(
        snapshot=snapshot,
        mappings=mappings,
        games=games,
        releases=releases,
        series=series,
        series_memberships=series_memberships,
    )

    mapped_data = mapper.map()
    pprint(mapped_data)
