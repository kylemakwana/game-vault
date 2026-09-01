import sqlite3

import pytest

from game_vault.databases.schema import create_tables
from game_vault.databases.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.models.mapping import SourceGameMapping


@pytest.fixture
def connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    create_tables(connection)

    # Parent records required by the foreign keys.
    connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name
        )
        VALUES (?, ?, ?)
        """,
        (
            "minecraft",
            "Minecraft",
            "Minecraft",
        ),
    )

    connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "minecraft-ps5",
            "minecraft",
            "ps5",
            "Minecraft",
        ),
    )

    connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "minecraft-ps4",
            "minecraft",
            "ps4",
            "Minecraft",
        ),
    )

    connection.commit()

    yield connection

    connection.close()


@pytest.fixture
def repository(
    connection: sqlite3.Connection,
) -> SourceGameMappingRepository:
    return SourceGameMappingRepository(connection)


@pytest.fixture
def source_mapping() -> SourceGameMapping:
    return SourceGameMapping(
        source="playstation",
        source_id="PPSA17221_00",
        game_release_id="minecraft-ps5",
        match_method="manual",
        confidence=1.0,
    )


def test_upsert_inserts_source_game_mapping(
    repository: SourceGameMappingRepository,
    source_mapping: SourceGameMapping,
) -> None:
    repository.upsert(source_mapping)

    result = repository.get(
        source_mapping.source,
        source_mapping.source_id,
    )

    assert result == source_mapping


def test_get_returns_source_game_mapping(
    repository: SourceGameMappingRepository,
    source_mapping: SourceGameMapping,
) -> None:
    repository.upsert(source_mapping)

    result = repository.get(
        "playstation",
        "PPSA17221_00",
    )

    assert isinstance(result, SourceGameMapping)
    assert result.source == "playstation"
    assert result.source_id == "PPSA17221_00"
    assert result.game_release_id == "minecraft-ps5"
    assert result.match_method == "manual"
    assert result.confidence == 1.0


def test_get_returns_none_when_mapping_does_not_exist(
    repository: SourceGameMappingRepository,
) -> None:
    result = repository.get(
        "playstation",
        "does-not-exist",
    )

    assert result is None


def test_get_requires_matching_source(
    repository: SourceGameMappingRepository,
    source_mapping: SourceGameMapping,
) -> None:
    repository.upsert(source_mapping)

    result = repository.get(
        "steam",
        source_mapping.source_id,
    )

    assert result is None


def test_get_by_game_release_id_returns_matching_mappings(
    repository: SourceGameMappingRepository,
) -> None:
    mappings = [
        SourceGameMapping(
            source="playstation",
            source_id="PPSA17221_00",
            game_release_id="minecraft-ps5",
            match_method="manual",
            confidence=1.0,
        ),
        SourceGameMapping(
            source="playstation",
            source_id="minecraft-store-id",
            game_release_id="minecraft-ps5",
            match_method="manual",
            confidence=1.0,
        ),
        SourceGameMapping(
            source="playstation",
            source_id="minecraft-ps4-id",
            game_release_id="minecraft-ps4",
            match_method="manual",
            confidence=1.0,
        ),
    ]

    for mapping in mappings:
        repository.upsert(mapping)

    result = repository.get_by_game_release_id("minecraft-ps5")

    assert len(result) == 2
    assert all(mapping.game_release_id == "minecraft-ps5" for mapping in result)


def test_get_by_game_release_id_returns_empty_list_when_none_exist(
    repository: SourceGameMappingRepository,
) -> None:
    result = repository.get_by_game_release_id("minecraft-ps5")

    assert result == []


def test_get_all_returns_all_source_game_mappings(
    repository: SourceGameMappingRepository,
) -> None:
    first_mapping = SourceGameMapping(
        source="playstation",
        source_id="PPSA17221_00",
        game_release_id="minecraft-ps5",
        match_method="manual",
        confidence=1.0,
    )

    second_mapping = SourceGameMapping(
        source="playstation",
        source_id="minecraft-ps4-id",
        game_release_id="minecraft-ps4",
        match_method="manual",
        confidence=1.0,
    )

    repository.upsert(first_mapping)
    repository.upsert(second_mapping)

    result = repository.get_all()

    assert len(result) == 2
    assert first_mapping in result
    assert second_mapping in result


def test_get_all_returns_empty_list_when_no_mappings_exist(
    repository: SourceGameMappingRepository,
) -> None:
    result = repository.get_all()

    assert result == []


def test_upsert_updates_existing_mapping(
    repository: SourceGameMappingRepository,
    source_mapping: SourceGameMapping,
) -> None:
    repository.upsert(source_mapping)

    updated_mapping = SourceGameMapping(
        source="playstation",
        source_id="PPSA17221_00",
        game_release_id="minecraft-ps4",
        match_method="external_id",
        confidence=0.95,
    )

    repository.upsert(updated_mapping)

    result = repository.get(
        "playstation",
        "PPSA17221_00",
    )

    assert result == updated_mapping
    assert len(repository.get_all()) == 1


def test_same_source_id_can_exist_for_different_sources(
    repository: SourceGameMappingRepository,
) -> None:
    playstation_mapping = SourceGameMapping(
        source="playstation",
        source_id="12345",
        game_release_id="minecraft-ps5",
        match_method="manual",
        confidence=1.0,
    )

    steam_mapping = SourceGameMapping(
        source="steam",
        source_id="12345",
        game_release_id="minecraft-ps4",
        match_method="manual",
        confidence=1.0,
    )

    repository.upsert(playstation_mapping)
    repository.upsert(steam_mapping)

    result = repository.get_all()

    assert len(result) == 2
    assert playstation_mapping in result
    assert steam_mapping in result


def test_delete_removes_existing_mapping(
    repository: SourceGameMappingRepository,
    source_mapping: SourceGameMapping,
) -> None:
    repository.upsert(source_mapping)

    result = repository.delete(
        source_mapping.source,
        source_mapping.source_id,
    )

    assert result is True
    assert (
        repository.get(
            source_mapping.source,
            source_mapping.source_id,
        )
        is None
    )


def test_delete_returns_false_when_mapping_does_not_exist(
    repository: SourceGameMappingRepository,
) -> None:
    result = repository.delete(
        "does-not-exist",
        "playstation",
    )

    assert result is False
