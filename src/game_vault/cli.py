"""Provide the Game Vault command-line interface."""

import argparse
from pathlib import Path

from game_vault.databases.achievement_group_repository import AchievementGroupRepository
from game_vault.databases.achievement_progress_repository import (
    AchievementProgressRepository,
)
from game_vault.databases.achievement_repository import AchievementRepository
from game_vault.databases.connection import get_connection
from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.databases.game_release_repository import GameReleaseRepository
from game_vault.databases.game_repository import GameRepository
from game_vault.databases.play_activity_repository import PlayActivityRepository
from game_vault.databases.schema import create_tables, drop_tables
from game_vault.databases.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.loaders.catalog_loader import load_catalog
from game_vault.mappers.playstation_mapper import PlayStationMappedData
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.playstation import PlayStationSnapshot
from game_vault.models.series import GameSeries, GameSeriesMembership
from game_vault.services.playstation_import_service import PlaystationImportService


def main() -> None:
    """Parse command-line arguments and dispatch the selected platform command."""
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

    psn_subparsers.add_parser(
        "import",
        help="Import the PlayStation data",
    )

    args = parser.parse_args()

    if args.platform == "psn":
        handle_psn_command(args.command)


def handle_psn_command(command: str) -> None:
    """Dispatch a PlayStation command.

    :param command: PlayStation subcommand selected by the user.
    """
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

    elif command == "import":
        import_playstation()


def collect_playstation_data() -> None:
    """Collect PlayStation account data and cache it locally."""
    from game_vault.collectors.playstation_collector import (
        PlayStationCollector,
    )
    from game_vault.playstation_client import create_psn_client

    client = create_psn_client()

    collector = PlayStationCollector(client)
    collector.collect_all()


def build_playstation_snapshot(write_output: bool = True) -> PlayStationSnapshot:
    """Build and write a normalized PlayStation snapshot from cached data."""
    from pathlib import Path

    from game_vault.services.playstation_snapshot_builder import (
        PlayStationSnapshotBuilder,
    )

    builder = PlayStationSnapshotBuilder()
    snapshot = builder.build()
    builder.validate()

    if write_output:
        output_path = Path("data/playstation/snapshot.json")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            snapshot.model_dump_json(indent=4),
            encoding="utf-8",
        )

        print(f"Snapshot written to {output_path.as_posix()}")

    return snapshot


def validate_playstation_snapshot() -> None:
    """Validate cached PlayStation data and print the validation summary."""
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


def map_playstation_snapshot(
    snapshot: PlayStationSnapshot | None = None,
) -> PlayStationMappedData:
    """Map the cached PlayStation snapshot into Game Vault domain records."""
    from game_vault.mappers.playstation_mapper import (
        PlayStationMapper,
    )
    from game_vault.services.playstation_snapshot_builder import (
        PlayStationSnapshotBuilder,
    )

    mappings = load_catalog(
        Path("resources/mappings/playstation.json"), SourceGameMapping
    )
    games = load_catalog(Path("resources/catalogue/games.json"), Game)
    releases = load_catalog(Path("resources/catalogue/releases.json"), GameRelease)
    series = load_catalog(Path("resources/catalogue/series.json"), GameSeries)
    series_memberships = load_catalog(
        Path("resources/catalogue/series_memberships.json"), GameSeriesMembership
    )

    if not snapshot:
        builder = PlayStationSnapshotBuilder()
        snapshot = builder.build()

    mapper = PlayStationMapper(
        snapshot=snapshot,
        mappings=mappings,
        games=games,
        releases=releases,
        series=series,
        series_memberships=series_memberships,
    )

    return mapper.map()


def import_playstation() -> None:
    """Run the PlayStation import workflow."""
    playstation_snapshot = build_playstation_snapshot()

    mapped_data = map_playstation_snapshot(
        snapshot=playstation_snapshot,
    )

    with get_connection() as connection:
        drop_tables(connection)
        create_tables(connection)

        game_repository = GameRepository(connection)
        game_release_repository = GameReleaseRepository(connection)
        external_identifier_repository = ExternalIdentifierRepository(connection)
        source_game_mapping_repository = SourceGameMappingRepository(connection)
        achievement_repository = AchievementRepository(connection)
        achievement_group_repository = AchievementGroupRepository(connection)
        achievement_progress_repository = AchievementProgressRepository(connection)
        play_activity_repository = PlayActivityRepository(connection)

        playstation_import_service = PlaystationImportService(
            game_repository=game_repository,
            game_release_repository=game_release_repository,
            external_identifier_repository=external_identifier_repository,
            source_game_mapping_repository=source_game_mapping_repository,
            achievement_repository=achievement_repository,
            achievement_group_repository=achievement_group_repository,
            achievement_progress_repository=achievement_progress_repository,
            play_activity_repository=play_activity_repository,
        )

        playstation_import_service.import_data(mapped_data)
