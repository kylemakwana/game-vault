from unittest.mock import Mock, call, create_autospec

import pytest

from game_vault.database.game_release_repository import GameReleaseRepository
from game_vault.database.game_repository import GameRepository
from game_vault.database.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping
from game_vault.services.catalog_service import CatalogService


@pytest.fixture
def game_repository() -> Mock:
    return create_autospec(GameRepository, instance=True)


@pytest.fixture
def game_release_repository() -> Mock:
    return create_autospec(GameReleaseRepository, instance=True)


@pytest.fixture
def source_game_mapping_repository() -> Mock:
    return create_autospec(SourceGameMappingRepository, instance=True)


@pytest.fixture
def catalog_service(
    game_repository: Mock,
    game_release_repository: Mock,
    source_game_mapping_repository: Mock,
) -> CatalogService:
    return CatalogService(
        game_repository,
        game_release_repository,
        source_game_mapping_repository,
    )


@pytest.fixture
def game() -> Game:
    return Game(
        id="minecraft",
        name="Minecraft",
        sort_name="minecraft",
    )


@pytest.fixture
def releases() -> list[GameRelease]:
    return [
        GameRelease(
            id="minecraft-ps4",
            game_id="minecraft",
            platform_id="ps4",
            name="Minecraft: PlayStation 4 Edition",
        ),
        GameRelease(
            id="minecraft-ps5",
            game_id="minecraft",
            platform_id="ps5",
            name="Minecraft",
        ),
    ]


@pytest.fixture
def mappings() -> list[SourceGameMapping]:
    return [
        SourceGameMapping(
            source="playstation",
            source_id="CUSA00265_00",
            game_release_id="minecraft-ps4",
            match_method="manual",
            confidence=1.0,
        ),
        SourceGameMapping(
            source="playstation",
            source_id="PPSA17221_00",
            game_release_id="minecraft-ps5",
            match_method="manual",
            confidence=1.0,
        ),
    ]


def test_save_game_upserts_game_releases_and_mappings(
    catalog_service: CatalogService,
    game_repository: Mock,
    game_release_repository: Mock,
    source_game_mapping_repository: Mock,
    game: Game,
    releases: list[GameRelease],
    mappings: list[SourceGameMapping],
) -> None:
    catalog_service.save_game(game, releases, mappings)

    game_repository.upsert.assert_called_once_with(game)
    assert game_release_repository.upsert.call_args_list == [
        call(releases[0]),
        call(releases[1]),
    ]
    assert source_game_mapping_repository.upsert.call_args_list == [
        call(mappings[0]),
        call(mappings[1]),
    ]


def test_save_game_accepts_empty_releases_and_mappings(
    catalog_service: CatalogService,
    game_repository: Mock,
    game_release_repository: Mock,
    source_game_mapping_repository: Mock,
    game: Game,
) -> None:
    catalog_service.save_game(game, [], [])

    game_repository.upsert.assert_called_once_with(game)
    game_release_repository.upsert.assert_not_called()
    source_game_mapping_repository.upsert.assert_not_called()


def test_get_game_returns_repository_result(
    catalog_service: CatalogService,
    game_repository: Mock,
    game: Game,
) -> None:
    game_repository.get.return_value = game

    result = catalog_service.get_game(game.id)

    assert result is game
    game_repository.get.assert_called_once_with(game.id)


def test_get_releases_for_game_returns_repository_result(
    catalog_service: CatalogService,
    game_release_repository: Mock,
    releases: list[GameRelease],
) -> None:
    game_release_repository.get_by_game_id.return_value = releases

    result = catalog_service.get_releases_for_game("minecraft")

    assert result is releases
    game_release_repository.get_by_game_id.assert_called_once_with("minecraft")


def test_delete_game_returns_repository_result(
    catalog_service: CatalogService,
    game_repository: Mock,
) -> None:
    game_repository.delete.return_value = True

    result = catalog_service.delete_game("minecraft")

    assert result is True
    game_repository.delete.assert_called_once_with("minecraft")


def test_get_mappings_for_release_returns_repository_result(
    catalog_service: CatalogService,
    source_game_mapping_repository: Mock,
    mappings: list[SourceGameMapping],
) -> None:
    source_game_mapping_repository.get_by_game_release_id.return_value = mappings

    result = catalog_service.get_mappings_for_release("minecraft-ps4")

    assert result is mappings
    source_game_mapping_repository.get_by_game_release_id.assert_called_once_with(
        "minecraft-ps4"
    )


def test_find_release_by_source_returns_none_when_mapping_does_not_exist(
    catalog_service: CatalogService,
    game_release_repository: Mock,
    source_game_mapping_repository: Mock,
) -> None:
    source_game_mapping_repository.get.return_value = None

    result = catalog_service.find_release_by_source(
        "playstation",
        "does-not-exist",
    )

    assert result is None
    source_game_mapping_repository.get.assert_called_once_with(
        "playstation",
        "does-not-exist",
    )
    game_release_repository.get.assert_not_called()


def test_find_release_by_source_returns_mapped_release(
    catalog_service: CatalogService,
    game_release_repository: Mock,
    source_game_mapping_repository: Mock,
    releases: list[GameRelease],
    mappings: list[SourceGameMapping],
) -> None:
    mapping = mappings[0]
    release = releases[0]
    source_game_mapping_repository.get.return_value = mapping
    game_release_repository.get.return_value = release

    result = catalog_service.find_release_by_source(
        mapping.source,
        mapping.source_id,
    )

    assert result is release
    source_game_mapping_repository.get.assert_called_once_with(
        mapping.source,
        mapping.source_id,
    )
    game_release_repository.get.assert_called_once_with(mapping.game_release_id)
