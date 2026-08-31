from game_vault.database.game_repository import GameRepository
from game_vault.models.game import Game


def test_row_to_game_converts_database_row(
    db_connection,
    stored_game,
):
    row = db_connection.execute(
        """
        SELECT *
        FROM game
        WHERE id = ?
        """,
        (stored_game.id,),
    ).fetchone()

    result = GameRepository._row_to_game(row)

    assert isinstance(result, Game)

    assert result.id == "minecraft"
    assert result.name == "Minecraft"
    assert result.sort_name == "minecraft"
    assert result.developer == "Mojang Studios"
    assert result.publisher == "Mojang Studios"
    assert result.genres == ["Sandbox", "Survival"]
    assert result.image_url == "https://example.com/minecraft.png"


def test_get_returns_game(
    db_connection,
    stored_game,
):
    repository = GameRepository(db_connection)

    result = repository.get(stored_game.id)

    assert result is not None

    assert result.id == stored_game.id
    assert result.name == stored_game.name
    assert result.sort_name == stored_game.sort_name
    assert result.release_date == stored_game.release_date
    assert result.developer == stored_game.developer
    assert result.publisher == stored_game.publisher
    assert result.genres == stored_game.genres
    assert result.image_url == stored_game.image_url


def test_get_returns_none_when_game_does_not_exist(
    db_connection,
):
    repository = GameRepository(db_connection)

    result = repository.get("does-not-exist")

    assert result is None


def test_get_all_returns_empty_list_when_no_games_exist(
    db_connection,
):
    repository = GameRepository(db_connection)

    result = repository.get_all()

    assert result == []


def test_get_all_returns_all_games(
    db_connection,
    game,
    second_game,
):
    repository = GameRepository(db_connection)

    repository.upsert(game)
    repository.upsert(second_game)

    result = repository.get_all()

    assert len(result) == 2

    assert {stored_game.id for stored_game in result} == {
        "minecraft",
        "stardew-valley",
    }


def test_upsert_inserts_game(
    db_connection,
    game,
):
    repository = GameRepository(db_connection)

    repository.upsert(game)

    row = db_connection.execute(
        """
        SELECT *
        FROM game
        WHERE id = ?
        """,
        (game.id,),
    ).fetchone()

    assert row is not None

    assert row["id"] == "minecraft"
    assert row["name"] == "Minecraft"
    assert row["sort_name"] == "minecraft"
    assert row["release_date"] == "2011-11-18"
    assert row["developer"] == "Mojang Studios"
    assert row["publisher"] == "Mojang Studios"
    assert row["genres"] == "Sandbox, Survival"
    assert row["image_url"] == "https://example.com/minecraft.png"


def test_upsert_commits_insert(
    db_connection,
    game,
):
    repository = GameRepository(db_connection)

    repository.upsert(game)

    assert db_connection.in_transaction is False


def test_upsert_updates_existing_game(
    db_connection,
    game,
):
    repository = GameRepository(db_connection)

    repository.upsert(game)

    updated_game = Game.model_validate(
        {
            "id": game.id,
            "name": "Minecraft Updated",
            "sort_name": "minecraft updated",
            "release_date": "2011-11-19",
            "developer": "Updated Developer",
            "publisher": "Updated Publisher",
            "genres": ["Adventure"],
            "image_url": "https://example.com/updated.png",
        }
    )

    repository.upsert(updated_game)

    result = repository.get(game.id)

    assert result is not None

    assert result.name == "Minecraft Updated"
    assert result.sort_name == "minecraft updated"
    assert result.release_date == updated_game.release_date
    assert result.developer == "Updated Developer"
    assert result.publisher == "Updated Publisher"
    assert result.genres == ["Adventure"]
    assert result.image_url == "https://example.com/updated.png"


def test_upsert_preserves_existing_nullable_metadata_when_new_values_are_none(
    db_connection,
    game,
):
    repository = GameRepository(db_connection)

    repository.upsert(game)

    updated_game = Game.model_validate(
        {
            "id": game.id,
            "name": "Minecraft Updated",
            "sort_name": "minecraft updated",
            "release_date": None,
            "developer": None,
            "publisher": None,
            "genres": ["Sandbox", "Survival"],
            "image_url": None,
        }
    )

    repository.upsert(updated_game)

    result = repository.get(game.id)

    assert result is not None

    assert result.name == "Minecraft Updated"
    assert result.sort_name == "minecraft updated"

    assert result.release_date == game.release_date
    assert result.developer == game.developer
    assert result.publisher == game.publisher
    assert result.image_url == game.image_url


def test_upsert_does_not_create_duplicate_game(
    db_connection,
    game,
):
    repository = GameRepository(db_connection)

    repository.upsert(game)
    repository.upsert(game)

    count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM game
        WHERE id = ?
        """,
        (game.id,),
    ).fetchone()[0]

    assert count == 1


def test_upsert_round_trips_empty_genres(
    db_connection,
):
    repository = GameRepository(db_connection)

    game = Game.model_validate(
        {
            "id": "test-game",
            "name": "Test Game",
            "sort_name": "test game",
            "release_date": None,
            "developer": None,
            "publisher": None,
            "genres": [],
            "image_url": None,
        }
    )

    repository.upsert(game)

    result = repository.get(game.id)

    assert result is not None
    assert result.genres == []


def test_delete_removes_existing_game(
    db_connection,
    stored_game,
):
    repository = GameRepository(db_connection)

    result = repository.delete(stored_game.id)

    assert result is True
    assert repository.get(stored_game.id) is None


def test_delete_returns_false_when_game_does_not_exist(
    db_connection,
):
    repository = GameRepository(db_connection)

    result = repository.delete("does-not-exist")

    assert result is False


def test_delete_commits_transaction(
    db_connection,
    stored_game,
):
    repository = GameRepository(db_connection)

    repository.delete(stored_game.id)

    assert db_connection.in_transaction is False


def test_delete_cascades_to_releases_identifiers_and_mappings(
    db_connection,
    stored_game_release,
    external_identifier,
):
    db_connection.execute(
        """
        INSERT INTO external_identifier (
            game_release_id,
            service,
            identifier_type,
            value
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            stored_game_release.id,
            external_identifier.service,
            external_identifier.identifier_type,
            external_identifier.value,
        ),
    )
    db_connection.execute(
        """
        INSERT INTO source_game_mapping (
            source,
            source_id,
            game_release_id,
            match_method,
            confidence
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "playstation",
            "PPSA17221_00",
            stored_game_release.id,
            "manual",
            1.0,
        ),
    )
    db_connection.commit()

    repository = GameRepository(db_connection)

    assert repository.delete(stored_game_release.game_id) is True

    for table in (
        "game_release",
        "external_identifier",
        "source_game_mapping",
    ):
        count = db_connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        assert count == 0
