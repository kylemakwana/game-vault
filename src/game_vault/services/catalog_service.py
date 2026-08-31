from game_vault.database.game_release_repository import GameReleaseRepository
from game_vault.database.game_repository import GameRepository
from game_vault.database.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping


class CatalogService:
    def __init__(
        self,
        game_repository: GameRepository,
        game_release_repository: GameReleaseRepository,
        source_game_mapping_repository: SourceGameMappingRepository,
    ) -> None:
        self.game_repository = game_repository
        self.game_release_repository = game_release_repository
        self.source_game_mapping_repository = source_game_mapping_repository

    def save_game(
        self,
        game: Game,
        releases: list[GameRelease],
        mappings: list[SourceGameMapping],
    ) -> None:
        self.game_repository.upsert(game)

        for release in releases:
            self.game_release_repository.upsert(release)

        for mapping in mappings:
            self.source_game_mapping_repository.upsert(mapping)

    def get_game(self, game_id: str) -> Game | None:
        return self.game_repository.get(game_id)

    def get_releases_for_game(
        self,
        game_id: str,
    ) -> list[GameRelease]:
        return self.game_release_repository.get_by_game_id(game_id)

    def delete_game(self, game_id: str) -> bool:
        return self.game_repository.delete(game_id)

    def get_mappings_for_release(
        self,
        game_release_id: str,
    ) -> list[SourceGameMapping]:
        return self.source_game_mapping_repository.get_by_game_release_id(
            game_release_id
        )

    def find_release_by_source(
        self,
        source: str,
        source_id: str,
    ) -> GameRelease | None:
        mapping = self.source_game_mapping_repository.get(
            source,
            source_id,
        )

        if mapping is None:
            return None

        return self.game_release_repository.get(mapping.game_release_id)
