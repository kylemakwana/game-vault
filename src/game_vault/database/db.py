from datetime import date, datetime

from game_vault.database.connection import get_connection
from game_vault.database.game_release_repository import GameReleaseRepository
from game_vault.database.game_repository import GameRepository
from game_vault.database.schema import create_tables, drop_tables
from game_vault.models.game import Game, GameRelease
from game_vault.models.platform import ExternalIdentifier


def main():
    connection = get_connection()
    drop_tables(connection)
    create_tables(connection)
    game_repository = GameRepository(connection)
    game_release_repository = GameReleaseRepository(connection)

    game = Game(
        id="minecraft",
        name="Minecraft",
        sort_name="Minecraft",
        release_date=datetime.strptime("2011-11-18", "%Y-%m-%d"),
        developer="Mojang Studios",
        publisher="Mojang Studios",
        genres=["Sandbox", "Survival"],
        image_url="...",
    )

    game_release = GameRelease(
        id="minecraft-ps5",
        game_id="minecraft",
        platform_id="ps5",
        name="Minecraft",
        release_date=date(2024, 10, 22),
        image_url=None,  # until we choose a proper image source
        external_identifiers=[
            ExternalIdentifier(
                service="playstation",
                identifier_type="product_id",
                value="PPSA17221_00",
            ),
        ],
    )

    game_repository.delete(game.id)
    game_repository.upsert(game)

    game_release_repository.delete(game_release.id)
    game_release_repository.upsert(game_release)

    game_release = game_release_repository.get(game_release.id)
    print(game_release)

    connection.close()


if __name__ == "__main__":
    main()
