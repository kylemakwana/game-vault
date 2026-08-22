from pathlib import Path

from game_vault.models.game import (
    Game,
    GameRelease,
)
from game_vault.models.platform import ExternalIdentifier


class PlaystationMapper:
    def __init__(
        self, snapshot_path: Path = Path("data/playstation/snapshots/snapshot.json")
    ):
        self.snapshot_path = snapshot_path

    @staticmethod
    def map() -> None:
        game: Game = Game(
            id="minecraft",
            name="Minecraft",
        )

        ps4_release: GameRelease = GameRelease(
            id="minecraft-ps4",
            game_id=game.id,
            platform_id="ps4",
            name="Minecraft: PlayStation®4 Edition",
            external_idenifiers=[
                ExternalIdentifier(
                    service="playstation_network",
                    identifier_type="title_id",
                    value="CUSA00265_00",
                )
            ],
        )

        ps5_release: GameRelease = GameRelease(
            id="minecraft-ps5",
            game_id=game.id,
            platform_id="ps5",
            name="Minecraft: PlayStation®5 Edition",
            external_idenifiers=[
                ExternalIdentifier(
                    service="playstation_network",
                    identifier_type="trophy_set_id",
                    value="NPWR41319_00",
                )
            ],
        )

        print(f"{game.id}")
        print(f"{game.name}")
        print(f"{ps4_release.id}")
        print(f"{ps5_release.id}")
