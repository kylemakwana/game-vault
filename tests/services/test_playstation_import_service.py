from unittest.mock import Mock

import pytest

from game_vault.database.connection import get_connection
from game_vault.database.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.database.game_release_repository import GameReleaseRepository
from game_vault.database.game_repository import GameRepository
from game_vault.database.schema import create_tables
from game_vault.database.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.mappers.playstation_mapper import PlaystationMappedData
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.platform import ExternalIdentifier
from game_vault.services import playstation_import_service
from game_vault.services.playstation_import_service import PlaystationImportService


@pytest.fixture
def connection():
    connection = get_connection(":memory:")
    create_tables(connection)

    yield connection

    connection.close()


@pytest.fixture
def game_repository(connection) -> GameRepository:
    return GameRepository(connection)


@pytest.fixture
def game_release_repository(connection) -> GameReleaseRepository:
    return GameReleaseRepository(connection)


@pytest.fixture
def external_identifier_repository(connection) -> ExternalIdentifierRepository:
    return ExternalIdentifierRepository(connection)


@pytest.fixture
def source_game_mapping_repository(connection) -> SourceGameMappingRepository:
    return SourceGameMappingRepository(connection)


@pytest.fixture
def import_service(
    game_repository,
    game_release_repository,
    external_identifier_repository,
    source_game_mapping_repository,
) -> PlaystationImportService:
    return PlaystationImportService(
        game_repository=game_repository,
        game_release_repository=game_release_repository,
        external_identifier_repository=external_identifier_repository,
        source_game_mapping_repository=source_game_mapping_repository,
    )


@pytest.fixture
def mapped_game() -> Game:
    return Game(
        id="minecraft",
        name="Minecraft",
        sort_name="minecraft",
    )


@pytest.fixture
def mapped_identifier() -> ExternalIdentifier:
    return ExternalIdentifier(
        service="playstation_network",
        identifier_type="title_id",
        value="CUSA00265_00",
    )


@pytest.fixture
def mapped_release(mapped_identifier) -> GameRelease:
    return GameRelease(
        id="minecraft-ps4",
        game_id="minecraft",
        platform_id="ps4",
        name="Minecraft: PlayStation 4 Edition",
        external_identifiers=[mapped_identifier],
    )


@pytest.fixture
def mapped_mapping() -> SourceGameMapping:
    return SourceGameMapping(
        source="playstation_title",
        source_id="CUSA00265_00",
        game_release_id="minecraft-ps4",
        match_method="external_id",
        confidence=1.0,
    )


@pytest.fixture
def mapped_data(
    mapped_game,
    mapped_release,
    mapped_mapping,
) -> PlaystationMappedData:
    return PlaystationMappedData(
        games=[mapped_game],
        releases=[mapped_release],
        mappings=[mapped_mapping],
    )


def patch_mapper(monkeypatch, mapped_data):
    mapper = Mock()
    mapper.map.return_value = mapped_data
    mapper_class = Mock(return_value=mapper)
    monkeypatch.setattr(
        playstation_import_service,
        "PlaystationMapper",
        mapper_class,
    )

    return mapper_class


def test_importing_mapped_snapshot_persists_catalogue_records(
    monkeypatch,
    import_service,
    game_repository,
    game_release_repository,
    external_identifier_repository,
    source_game_mapping_repository,
    mapped_data,
    mapped_game,
    mapped_release,
    mapped_identifier,
    mapped_mapping,
):
    patch_mapper(monkeypatch, mapped_data)
    snapshot = Mock()

    import_service.import_snapshot(snapshot)

    assert game_repository.get(mapped_game.id) == mapped_game
    assert game_release_repository.get(mapped_release.id) == mapped_release
    assert external_identifier_repository.get_all_for_release(mapped_release.id) == [
        mapped_identifier
    ]
    assert (
        source_game_mapping_repository.get(
            mapped_mapping.source,
            mapped_mapping.source_id,
        )
        == mapped_mapping
    )


def test_import_passes_existing_catalogue_state_to_mapper(
    monkeypatch,
    import_service,
    game_repository,
    game_release_repository,
    source_game_mapping_repository,
    mapped_game,
    mapped_release,
    mapped_mapping,
):
    game_repository.upsert(mapped_game)
    game_release_repository.upsert(mapped_release)
    source_game_mapping_repository.upsert(mapped_mapping)
    mapper_class = patch_mapper(
        monkeypatch,
        PlaystationMappedData(games=[]),
    )
    snapshot = Mock()

    import_service.import_snapshot(snapshot)

    mapper_class.assert_called_once_with(
        snapshot=snapshot,
        mappings=[mapped_mapping],
        releases=[mapped_release],
        games=[mapped_game],
        series=[],
        series_memberships=[],
    )


def test_importing_same_snapshot_twice_is_idempotent(
    monkeypatch,
    connection,
    import_service,
    game_repository,
    game_release_repository,
    source_game_mapping_repository,
    mapped_data,
):
    patch_mapper(monkeypatch, mapped_data)
    snapshot = Mock()

    import_service.import_snapshot(snapshot)
    state_after_first_import = (
        game_repository.get_all(),
        game_release_repository.get_all(),
        source_game_mapping_repository.get_all(),
    )

    import_service.import_snapshot(snapshot)
    state_after_second_import = (
        game_repository.get_all(),
        game_release_repository.get_all(),
        source_game_mapping_repository.get_all(),
    )

    assert state_after_second_import == state_after_first_import

    for table in (
        "game",
        "game_release",
        "external_identifier",
        "source_game_mapping",
    ):
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        assert count == 1
