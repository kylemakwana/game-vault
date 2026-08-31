import sqlite3

import pytest

from game_vault.database.game_release_repository import (
    GameReleaseRepository,
)
from game_vault.database.game_repository import GameRepository
from game_vault.models.game import GameRelease


def test_get_returns_game_release(
    db_connection,
    stored_game_release,
):
    repository = GameReleaseRepository(db_connection)

    result = repository.get(stored_game_release.id)

    assert result is not None

    assert result.id == stored_game_release.id
    assert result.game_id == stored_game_release.game_id
    assert result.platform_id == stored_game_release.platform_id
    assert result.name == stored_game_release.name
    assert result.release_date == stored_game_release.release_date
    assert result.image_url == stored_game_release.image_url


def test_get_returns_none_when_release_does_not_exist(
    db_connection,
):
    repository = GameReleaseRepository(db_connection)

    result = repository.get("does-not-exist")

    assert result is None


def test_get_loads_external_identifiers(
    db_connection,
    stored_game_release,
    external_identifier,
    second_external_identifier,
):
    db_connection.executemany(
        """
        INSERT INTO external_identifier (
            game_release_id,
            service,
            identifier_type,
            value
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                stored_game_release.id,
                external_identifier.service,
                external_identifier.identifier_type,
                external_identifier.value,
            ),
            (
                stored_game_release.id,
                second_external_identifier.service,
                second_external_identifier.identifier_type,
                second_external_identifier.value,
            ),
        ],
    )

    db_connection.commit()

    repository = GameReleaseRepository(db_connection)

    result = repository.get(stored_game_release.id)

    assert result is not None
    assert len(result.external_identifiers) == 2

    values = {identifier.value for identifier in result.external_identifiers}

    assert values == {
        external_identifier.value,
        second_external_identifier.value,
    }


def test_get_by_game_id_returns_empty_list_when_game_has_no_releases(
    db_connection,
    stored_game,
):
    repository = GameReleaseRepository(db_connection)

    result = repository.get_by_game_id(stored_game.id)

    assert result == []


def test_get_by_game_id_returns_only_releases_for_requested_game(
    db_connection,
    stored_game,
    second_game,
    game_release,
):
    GameRepository(db_connection).upsert(second_game)
    repository = GameReleaseRepository(db_connection)

    second_release = game_release.model_copy(
        update={
            "id": "minecraft-ps5",
            "platform_id": "ps5",
            "name": "Minecraft PS5",
            "external_identifiers": [],
        }
    )
    unrelated_release = game_release.model_copy(
        update={
            "id": "stardew-valley-ps4",
            "game_id": second_game.id,
            "name": second_game.name,
            "external_identifiers": [],
        }
    )

    repository.upsert(game_release)
    repository.upsert(second_release)
    repository.upsert(unrelated_release)

    result = repository.get_by_game_id(stored_game.id)

    assert {release.id for release in result} == {
        game_release.id,
        second_release.id,
    }
    assert all(release.game_id == stored_game.id for release in result)


def test_get_by_game_id_loads_external_identifiers(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)
    repository.upsert(game_release)

    result = repository.get_by_game_id(stored_game.id)

    assert len(result) == 1
    assert result[0].external_identifiers == game_release.external_identifiers


def test_get_all_returns_empty_list_when_no_releases_exist(
    db_connection,
):
    repository = GameReleaseRepository(db_connection)

    result = repository.get_all()

    assert result == []


def test_get_all_returns_all_releases(
    db_connection,
    stored_game,
):
    db_connection.executemany(
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
        [
            (
                "minecraft-ps4",
                stored_game.id,
                "ps4",
                "Minecraft PS4",
                "2014-09-04",
                None,
            ),
            (
                "minecraft-ps5",
                stored_game.id,
                "ps5",
                "Minecraft PS5",
                "2021-01-01",
                None,
            ),
        ],
    )

    db_connection.commit()

    repository = GameReleaseRepository(db_connection)

    result = repository.get_all()

    assert len(result) == 2

    assert {release.id for release in result} == {
        "minecraft-ps4",
        "minecraft-ps5",
    }


def test_get_all_loads_external_identifiers(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    result = repository.get_all()

    assert len(result) == 1
    assert len(result[0].external_identifiers) == 2


def test_upsert_inserts_game_release(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    row = db_connection.execute(
        """
        SELECT *
        FROM game_release
        WHERE id = ?
        """,
        (game_release.id,),
    ).fetchone()

    assert row is not None

    assert row["id"] == game_release.id
    assert row["game_id"] == game_release.game_id
    assert row["platform_id"] == game_release.platform_id
    assert row["name"] == game_release.name
    assert row["release_date"] == "2014-09-04"
    assert row["image_url"] == game_release.image_url


def test_upsert_rejects_release_for_nonexistent_game(
    db_connection,
    game_release,
):
    repository = GameReleaseRepository(db_connection)
    orphaned_release = game_release.model_copy(update={"game_id": "does-not-exist"})

    with pytest.raises(sqlite3.IntegrityError):
        repository.upsert(orphaned_release)

    assert repository.get(orphaned_release.id) is None


def test_upsert_inserts_external_identifiers(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    rows = db_connection.execute(
        """
        SELECT
            service,
            identifier_type,
            value
        FROM external_identifier
        WHERE game_release_id = ?
        """,
        (game_release.id,),
    ).fetchall()

    assert len(rows) == 2

    assert {row["value"] for row in rows} == {
        identifier.value for identifier in game_release.external_identifiers
    }


def test_upsert_commits_release_and_external_identifiers_together(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    assert db_connection.in_transaction is False

    release_count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM game_release
        WHERE id = ?
        """,
        (game_release.id,),
    ).fetchone()[0]

    identifier_count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM external_identifier
        WHERE game_release_id = ?
        """,
        (game_release.id,),
    ).fetchone()[0]

    assert release_count == 1
    assert identifier_count == 2


def test_upsert_does_not_duplicate_external_identifiers(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)
    repository.upsert(game_release)

    count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM external_identifier
        WHERE game_release_id = ?
        """,
        (game_release.id,),
    ).fetchone()[0]

    assert count == 2


def test_upsert_updates_existing_release_name(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    updated_release = GameRelease.model_validate(
        {
            "id": game_release.id,
            "game_id": game_release.game_id,
            "platform_id": game_release.platform_id,
            "name": "Minecraft PS4 Updated",
            "release_date": game_release.release_date,
            "image_url": game_release.image_url,
            "external_identifiers": [],
        }
    )

    repository.upsert(updated_release)

    result = repository.get(game_release.id)

    assert result is not None
    assert result.name == "Minecraft PS4 Updated"


def test_upsert_preserves_release_date_when_new_value_is_none(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    updated_release = GameRelease.model_validate(
        {
            "id": game_release.id,
            "game_id": game_release.game_id,
            "platform_id": game_release.platform_id,
            "name": "Minecraft Updated",
            "release_date": None,
            "image_url": game_release.image_url,
            "external_identifiers": [],
        }
    )

    repository.upsert(updated_release)

    result = repository.get(game_release.id)

    assert result is not None
    assert result.release_date == game_release.release_date


def test_upsert_preserves_image_url_when_new_value_is_none(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)

    updated_release = GameRelease.model_validate(
        {
            "id": game_release.id,
            "game_id": game_release.game_id,
            "platform_id": game_release.platform_id,
            "name": "Minecraft Updated",
            "release_date": game_release.release_date,
            "image_url": None,
            "external_identifiers": [],
        }
    )

    repository.upsert(updated_release)

    result = repository.get(game_release.id)

    assert result is not None
    assert result.image_url == game_release.image_url


def test_upsert_does_not_create_duplicate_release(
    db_connection,
    stored_game,
    game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.upsert(game_release)
    repository.upsert(game_release)

    count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM game_release
        WHERE id = ?
        """,
        (game_release.id,),
    ).fetchone()[0]

    assert count == 1


def test_delete_removes_existing_release(
    db_connection,
    stored_game_release,
):
    repository = GameReleaseRepository(db_connection)

    result = repository.delete(stored_game_release.id)

    assert result is True
    assert repository.get(stored_game_release.id) is None


def test_delete_returns_false_when_release_does_not_exist(
    db_connection,
):
    repository = GameReleaseRepository(db_connection)

    result = repository.delete("does-not-exist")

    assert result is False


def test_delete_commits_transaction(
    db_connection,
    stored_game_release,
):
    repository = GameReleaseRepository(db_connection)

    repository.delete(stored_game_release.id)

    assert db_connection.in_transaction is False
