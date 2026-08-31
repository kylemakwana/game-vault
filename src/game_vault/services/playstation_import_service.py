"""Provide the service boundary for importing PlayStation snapshots."""

from game_vault.database.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.database.game_release_repository import GameReleaseRepository
from game_vault.database.game_repository import GameRepository
from game_vault.database.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.mappers.playstation_mapper import (
    PlaystationMappedData,
    PlaystationMapper,
)
from game_vault.models.playstation import PlayStationSnapshot


class PlaystationImportService:
    """Coordinate mapping and persistence of PlayStation snapshot data."""

    def __init__(
        self,
        game_repository: GameRepository,
        game_release_repository: GameReleaseRepository,
        external_identifier_repository: ExternalIdentifierRepository,
        source_game_mapping_repository: SourceGameMappingRepository,
    ):
        """Initialize the PlayStation import service."""
        self.game_repository = game_repository
        self.game_release_repository = game_release_repository
        self.external_identifier_repository = external_identifier_repository
        self.source_game_mapping_repository = source_game_mapping_repository

    def import_snapshot(self, snapshot: PlayStationSnapshot) -> None:
        """Import a PlayStation snapshot into Game Vault.

        :param snapshot: Normalized PlayStation snapshot to import.
        """
        existing_releases = self.game_release_repository.get_all()
        existing_games = self.game_repository.get_all()
        existing_mappings = self.source_game_mapping_repository.get_all()

        mapper = PlaystationMapper(
            snapshot=snapshot,
            mappings=existing_mappings,
            releases=existing_releases,
            games=existing_games,
            # Series persistence is not part of the initial import slice.
            series=[],
            series_memberships=[],
        )

        mapped_data: PlaystationMappedData = mapper.map()

        for game in mapped_data.games:
            self.game_repository.upsert(game)

        for release in mapped_data.releases:
            self.game_release_repository.upsert(release)

            for external_identifier in release.external_identifiers:
                self.external_identifier_repository.insert(
                    game_release_id=release.id,
                    external_identifier=external_identifier,
                )

        for mapping in mapped_data.mappings:
            self.source_game_mapping_repository.upsert(mapping)
