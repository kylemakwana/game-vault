"""Provide the service boundary for importing PlayStation snapshots."""

from game_vault.databases.achievement_group_repository import AchievementGroupRepository
from game_vault.databases.achievement_progress_repository import (
    AchievementProgressRepository,
)
from game_vault.databases.achievement_repository import AchievementRepository
from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.databases.game_release_repository import GameReleaseRepository
from game_vault.databases.game_repository import GameRepository
from game_vault.databases.play_activity_repository import PlayActivityRepository
from game_vault.databases.source_game_mapping_repository import (
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
        achievement_repository: AchievementRepository,
        achievement_group_repository: AchievementGroupRepository,
        achievement_progress_repository: AchievementProgressRepository,
        play_activity_repository: PlayActivityRepository,
    ):
        self.game_repository = game_repository
        self.game_release_repository = game_release_repository
        self.external_identifier_repository = external_identifier_repository
        self.source_game_mapping_repository = source_game_mapping_repository
        self.achievement_repository = achievement_repository
        self.achievement_group_repository = achievement_group_repository
        self.achievement_progress_repository = achievement_progress_repository
        self.play_activity_repository = play_activity_repository

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
        print(f"Importing {len(mapped_data.achievement_groups)} achievement groups...")

        for achievement_group in mapped_data.achievement_groups:
            self.achievement_group_repository.insert(achievement_group)

        print("Achievement groups imported!\n")
        print(f"Importing {len(mapped_data.achievements)} achievements...")

        for achievement in mapped_data.achievements:
            self.achievement_repository.upsert(achievement)

        print("Achievements imported!\n")

        print(
            f"Importing progress of {len(mapped_data.achievement_progress)} "
            f"achievements..."
        )

        for achievement_progress in mapped_data.achievement_progress:
            self.achievement_progress_repository.upsert(achievement_progress)

        print("Achievement progress imported!\n")
        print(f"Importing {len(mapped_data.activities)} play activities...")

        for activity in mapped_data.activities:
            self.play_activity_repository.upsert(activity)

        print("Activity imported!\n")
        print("Import successful! All PlayStation data imported!\n")
