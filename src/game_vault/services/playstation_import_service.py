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
    PlayStationMappedData,
)


class PlaystationImportService:
    """Persist mapped PlayStation data into Game Vault."""

    def __init__(
        self,
        game_repository: GameRepository,
        game_release_repository: GameReleaseRepository,
        external_identifier_repository: ExternalIdentifierRepository,
        source_game_mapping_repository: SourceGameMappingRepository,
    ):
        self.game_repository = game_repository
        self.game_release_repository = game_release_repository
        self.external_identifier_repository = external_identifier_repository
        self.source_game_mapping_repository = source_game_mapping_repository

    def import_data(self, mapped_data: PlayStationMappedData) -> None:
        """Import mapped PlayStation data into Game Vault."""
        print("Importing mapped PlayStation data...\n")
        print(f"Importing {len(mapped_data.games)} mapped games...")
        for game in mapped_data.games:
            self.game_repository.upsert(game)

        print("Games imported!\n")
        print(f"Importing {len(mapped_data.releases)} mapped releases...")

        for release in mapped_data.releases:
            self.game_release_repository.upsert(release)

            print(
                f"Importing {len(release.external_identifiers)} external identifiers "
                f"for {release.name}..."
            )
            for external_identifier in release.external_identifiers:
                self.external_identifier_repository.insert(
                    game_release_id=release.id,
                    external_identifier=external_identifier,
                )
            print(f"Imported external identifiers for {release.name}\n")

        print("Releases and external identifiers imported!\n")
        print(f"Importing {len(mapped_data.mappings)} source game mappings...")

        for mapping in mapped_data.mappings:
            self.source_game_mapping_repository.upsert(mapping)

        print("Mappings imported!\n")
        print("Import successful! All PlayStation data imported!\n")
