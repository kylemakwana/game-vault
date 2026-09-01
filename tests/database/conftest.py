import pytest

from game_vault.databases.connection import get_connection
from game_vault.databases.schema import create_tables
from game_vault.models.game import Game, GameRelease
from game_vault.models.platform import ExternalIdentifier


@pytest.fixture
def empty_db_connection():
    connection = get_connection(":memory:")

    yield connection

    connection.close()


@pytest.fixture
def db_connection(empty_db_connection):
    create_tables(empty_db_connection)

    return empty_db_connection


@pytest.fixture
def game():
    return Game.model_validate(
        {
            "id": "minecraft",
            "name": "Minecraft",
            "sort_name": "minecraft",
            "release_date": "2011-11-18",
            "developer": "Mojang Studios",
            "publisher": "Mojang Studios",
            "genres": [
                "Sandbox",
                "Survival",
            ],
            "image_url": "https://example.com/minecraft.png",
        }
    )


@pytest.fixture
def second_game():
    return Game.model_validate(
        {
            "id": "stardew-valley",
            "name": "Stardew Valley",
            "sort_name": "stardew valley",
            "release_date": "2016-02-26",
            "developer": "ConcernedApe",
            "publisher": "ConcernedApe",
            "genres": [
                "Simulation",
                "RPG",
            ],
            "image_url": "https://example.com/stardew.png",
        }
    )


@pytest.fixture
def external_identifier():
    return ExternalIdentifier.model_validate(
        {
            "service": "playstation_network",
            "identifier_type": "title_id",
            "value": "CUSA00265_00",
        }
    )


@pytest.fixture
def second_external_identifier():
    return ExternalIdentifier.model_validate(
        {
            "service": "playstation_network",
            "identifier_type": "trophy_set",
            "value": "NPWR05567_00",
        }
    )


@pytest.fixture
def game_release(
    external_identifier,
    second_external_identifier,
):
    return GameRelease.model_validate(
        {
            "id": "minecraft-ps4",
            "game_id": "minecraft",
            "platform_id": "ps4",
            "name": "Minecraft: PlayStation 4 Edition",
            "release_date": "2014-09-04",
            "image_url": "https://example.com/minecraft-ps4.png",
            "external_identifiers": [
                external_identifier,
                second_external_identifier,
            ],
        }
    )


@pytest.fixture
def stored_game(
    db_connection,
    game,
):
    db_connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name,
            release_date,
            developer,
            publisher,
            genres,
            image_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            game.id,
            game.name,
            game.sort_name,
            game.release_date.isoformat(),
            game.developer,
            game.publisher,
            ", ".join(game.genres),
            game.image_url,
        ),
    )

    db_connection.commit()

    return game


@pytest.fixture
def stored_game_release(
    db_connection,
    stored_game,
    game_release,
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
            game_release.id,
            game_release.game_id,
            game_release.platform_id,
            game_release.name,
            game_release.release_date.isoformat(),
            game_release.image_url,
        ),
    )

    db_connection.commit()

    return game_release
