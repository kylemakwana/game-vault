"""Coordinate catalog operations across persistence repositories."""

from game_vault.database.game_release_repository import GameReleaseRepository
from game_vault.database.game_repository import GameRepository
from game_vault.database.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping


class CatalogService:
    """Provide application-level operations for games and their releases."""

    def __init__(
        self,
        game_repository: GameRepository,
        game_release_repository: GameReleaseRepository,
        source_game_mapping_repository: SourceGameMappingRepository,
    ) -> None:
        """Initialize the catalog service.

        :param game_repository: Repository used to persist games.
        :param game_release_repository: Repository used to persist releases.
        :param source_game_mapping_repository: Repository used to persist source
            mappings.
        """
        self.game_repository = game_repository
        self.game_release_repository = game_release_repository
        self.source_game_mapping_repository = source_game_mapping_repository

    def save_game(
        self,
        game: Game,
        releases: list[GameRelease],
        mappings: list[SourceGameMapping],
    ) -> None:
        """Persist a game and its associated releases and source mappings.

        :param game: Game to persist.
        :param releases: Platform-specific releases belonging to the game.
        :param mappings: External-source mappings for the releases.
        """
        self.game_repository.upsert(game)

        for release in releases:
            self.game_release_repository.upsert(release)

        for mapping in mappings:
            self.source_game_mapping_repository.upsert(mapping)

    def get_game(self, game_id: str) -> Game | None:
        """Return a game by identifier.

        :param game_id: Catalog game identifier.
        :return: Matching game, or ``None`` when it does not exist.
        """
        return self.game_repository.get(game_id)

    def get_releases_for_game(
        self,
        game_id: str,
    ) -> list[GameRelease]:
        """Return all releases belonging to a game.

        :param game_id: Catalog game identifier.
        :return: Releases associated with the game.
        """
        return self.game_release_repository.get_by_game_id(game_id)

    def delete_game(self, game_id: str) -> bool:
        """Delete a game and its dependent catalog records.

        :param game_id: Catalog game identifier.
        :return: ``True`` when the game existed, otherwise ``False``.
        """
        return self.game_repository.delete(game_id)

    def get_mappings_for_release(
        self,
        game_release_id: str,
    ) -> list[SourceGameMapping]:
        """Return source mappings associated with a release.

        :param game_release_id: Catalog release identifier.
        :return: Source mappings that target the release.
        """
        return self.source_game_mapping_repository.get_by_game_release_id(
            game_release_id
        )

    def find_release_by_source(
        self,
        source: str,
        source_id: str,
    ) -> GameRelease | None:
        """Resolve an external source identifier to a game release.

        :param source: External source namespace.
        :param source_id: Identifier within the external source.
        :return: Mapped game release, or ``None`` when no mapping or release exists.
        """
        mapping = self.source_game_mapping_repository.get(
            source,
            source_id,
        )

        if mapping is None:
            return None

        return self.game_release_repository.get(mapping.game_release_id)
