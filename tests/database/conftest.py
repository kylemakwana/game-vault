import pytest

from game_vault.databases.connection import get_connection
from game_vault.databases.schema import create_tables
from game_vault.models.achievement import (
    Achievement,
    AchievementGroup,
    AchievementProgress,
)
from game_vault.models.activity import PlayActivity
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


@pytest.fixture
def achievement_group(stored_game_release):
    return AchievementGroup(
        id="minecraft-ps4-achievements-group-default",
        game_release_id=stored_game_release.id,
        external_group_id="default",
        name="Base Game",
    )


@pytest.fixture
def stored_achievement_group(
    db_connection,
    achievement_group,
):
    db_connection.execute(
        """
        INSERT INTO achievement_group (
            id,
            game_release_id,
            external_group_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            achievement_group.id,
            achievement_group.game_release_id,
            achievement_group.external_group_id,
            achievement_group.name,
        ),
    )
    db_connection.commit()

    return achievement_group


@pytest.fixture
def achievement(stored_achievement_group):
    return Achievement(
        id="minecraft-ps4-achievement-1",
        game_release_id=stored_achievement_group.game_release_id,
        group_id=stored_achievement_group.id,
        external_id="1",
        name="Taking Inventory",
        description="Open your inventory.",
        icon_url="https://example.com/trophy.png",
        hidden=False,
        achievement_type="bronze",
        rarity="common",
        global_unlock_percentage=80.5,
        progress_target=100,
    )


@pytest.fixture
def stored_achievement(
    db_connection,
    achievement,
):
    db_connection.execute(
        """
        INSERT INTO achievement (
            id,
            game_release_id,
            group_id,
            external_id,
            name,
            description,
            icon_url,
            hidden,
            achievement_type,
            rarity,
            global_unlock_percentage,
            progress_target
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            achievement.id,
            achievement.game_release_id,
            achievement.group_id,
            achievement.external_id,
            achievement.name,
            achievement.description,
            achievement.icon_url,
            achievement.hidden,
            achievement.achievement_type,
            achievement.rarity,
            achievement.global_unlock_percentage,
            achievement.progress_target,
        ),
    )
    db_connection.commit()

    return achievement


@pytest.fixture
def achievement_progress(stored_achievement):
    return AchievementProgress(
        achievement_id=stored_achievement.id,
        account_id="psn:123456789",
        unlocked=True,
        unlocked_at="2025-01-05T00:00:00Z",
        progress=100,
        progress_percentage=100,
        progressed_at="2025-01-05T00:00:00Z",
    )


@pytest.fixture
def play_activity(stored_game_release):
    return PlayActivity(
        id="ps-activity:CUSA00265_00",
        account_id="psn:123456789",
        game_release_id=stored_game_release.id,
        playtime_seconds=7200,
        play_count=4,
        first_played_at="2025-01-01T00:00:00Z",
        last_played_at="2025-01-10T00:00:00Z",
        source="PlayStation",
    )
