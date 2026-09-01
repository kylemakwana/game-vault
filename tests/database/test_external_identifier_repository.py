from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
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
