import pytest

from game_vault.config import IdentifierTypeEnum, PlatformEnum
from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
)


@pytest.mark.parametrize(
    ("service", "identifier_type", "value", "matches"),
    [
        (PlatformEnum.PLAYSTATION, IdentifierTypeEnum.TITLE_ID, "CUSA00265_00", True),
        (PlatformEnum.STEAM, IdentifierTypeEnum.TITLE_ID, "CUSA00265_00", False),
        (
            PlatformEnum.PLAYSTATION,
            IdentifierTypeEnum.NP_TITLE_ID,
            "CUSA00265_00",
            False,
        ),
        (PlatformEnum.PLAYSTATION, IdentifierTypeEnum.TITLE_ID, "missing", False),
        (PlatformEnum.PLAYSTATION, IdentifierTypeEnum.TITLE_ID, "' OR 1=1 --", False),
    ],
)
def test_find_game_release_ids_filters_all_identifier_fields(
    db_connection,
    stored_game_release,
    external_identifier,
    service,
    identifier_type,
    value,
    matches,
):
    repository = ExternalIdentifierRepository(db_connection)
    repository.insert(stored_game_release.id, external_identifier)
    assert repository.find_game_release_ids(service, identifier_type, value) == (
        [stored_game_release.id] if matches else []
    )


def test_find_game_release_ids_returns_all_matching_releases(
    db_connection,
    stored_game_release,
    external_identifier,
):
    db_connection.execute(
        "INSERT INTO game_release (id, game_id, platform_id, name) VALUES (?, ?, ?, ?)",
        ("minecraft-ps5", stored_game_release.game_id, "ps5", "Minecraft"),
    )
    repository = ExternalIdentifierRepository(db_connection)
    for release_id in (stored_game_release.id, "minecraft-ps5"):
        repository.insert(release_id, external_identifier)
    assert set(
        repository.find_game_release_ids(
            PlatformEnum.PLAYSTATION, IdentifierTypeEnum.TITLE_ID, "CUSA00265_00"
        )
    ) == {stored_game_release.id, "minecraft-ps5"}


def test_find_game_release_ids_returns_empty_without_identifiers(db_connection):
    repository = ExternalIdentifierRepository(db_connection)
    assert (
        repository.find_game_release_ids(
            PlatformEnum.PLAYSTATION, IdentifierTypeEnum.TITLE_ID, "missing"
        )
        == []
    )


def test_get_all_for_release_returns_empty_list(
    db_connection,
    stored_game_release,
):
    repository = ExternalIdentifierRepository(db_connection)

    result = repository.get_all_for_release(stored_game_release.id)

    assert result == []


def test_insert_adds_external_identifier(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    result = repository.get_all_for_release(stored_game_release.id)

    assert len(result) == 1

    assert result[0].service == external_identifier.service
    assert result[0].identifier_type == external_identifier.identifier_type
    assert result[0].value == external_identifier.value


def test_insert_commits_by_default(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    assert db_connection.in_transaction is False


def test_insert_can_skip_commit(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
        commit=False,
    )

    assert db_connection.in_transaction is True

    db_connection.rollback()

    result = repository.get_all_for_release(stored_game_release.id)

    assert result == []


def test_insert_duplicate_does_not_create_duplicate_record(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    result = repository.get_all_for_release(stored_game_release.id)

    assert len(result) == 1


def test_get_all_for_release_returns_all_external_identifiers(
    db_connection,
    stored_game_release,
    external_identifier,
    second_external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    repository.insert(
        stored_game_release.id,
        second_external_identifier,
    )

    result = repository.get_all_for_release(stored_game_release.id)

    assert len(result) == 2

    values = {identifier.value for identifier in result}

    assert values == {
        external_identifier.value,
        second_external_identifier.value,
    }


def test_get_all_for_release_only_returns_identifiers_for_requested_release(
    db_connection,
    stored_game,
    stored_game_release,
    external_identifier,
):
    db_connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name,
            release_date,
            image_url
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "minecraft-ps5",
            stored_game.id,
            "ps5",
            "Minecraft",
            "2021-01-01",
            None,
        ),
    )

    db_connection.commit()

    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    repository.insert(
        "minecraft-ps5",
        external_identifier,
    )

    result = repository.get_all_for_release(stored_game_release.id)

    assert len(result) == 1


def test_delete_removes_external_identifier(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    result = repository.delete(
        stored_game_release.id,
        external_identifier,
    )

    assert result is True

    assert repository.get_all_for_release(stored_game_release.id) == []


def test_delete_only_removes_matching_external_identifier(
    db_connection,
    stored_game_release,
    external_identifier,
    second_external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    repository.insert(
        stored_game_release.id,
        second_external_identifier,
    )

    repository.delete(
        stored_game_release.id,
        external_identifier,
    )

    result = repository.get_all_for_release(stored_game_release.id)

    assert len(result) == 1
    assert result[0].value == second_external_identifier.value


def test_delete_returns_false_when_identifier_does_not_exist(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    result = repository.delete(
        stored_game_release.id,
        external_identifier,
    )

    assert result is False


def test_delete_commits_transaction(
    db_connection,
    stored_game_release,
    external_identifier,
):
    repository = ExternalIdentifierRepository(db_connection)

    repository.insert(
        stored_game_release.id,
        external_identifier,
    )

    repository.delete(
        stored_game_release.id,
        external_identifier,
    )

    assert db_connection.in_transaction is False
