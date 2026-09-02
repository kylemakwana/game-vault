import pytest

from game_vault.databases.achievement_group_repository import AchievementGroupRepository
from game_vault.databases.achievement_progress_repository import (
    AchievementProgressRepository,
)
from game_vault.databases.achievement_repository import AchievementRepository
from game_vault.databases.connection import get_connection
from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.databases.game_release_repository import GameReleaseRepository
from game_vault.databases.game_repository import GameRepository
from game_vault.databases.play_activity_repository import PlayActivityRepository
from game_vault.databases.schema import create_tables
from game_vault.databases.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.mappers.playstation_mapper import PlayStationMappedData
from game_vault.models.achievement import (
    Achievement,
    AchievementGroup,
    AchievementProgress,
)
from game_vault.models.activity import PlayActivity
from game_vault.models.game import Game, GameRelease
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.platform import ExternalIdentifier
from game_vault.services.playstation_import_service import PlaystationImportService


@pytest.fixture
def connection():
    connection = get_connection(":memory:")
    create_tables(connection)

    yield connection

    connection.close()


@pytest.fixture
def game_repository(connection) -> GameRepository:
    return GameRepository(connection)


@pytest.fixture
def game_release_repository(connection) -> GameReleaseRepository:
    return GameReleaseRepository(connection)


@pytest.fixture
def external_identifier_repository(connection) -> ExternalIdentifierRepository:
    return ExternalIdentifierRepository(connection)


@pytest.fixture
def source_game_mapping_repository(connection) -> SourceGameMappingRepository:
    return SourceGameMappingRepository(connection)


@pytest.fixture
def achievement_repository(connection) -> AchievementRepository:
    return AchievementRepository(connection)


@pytest.fixture
def achievement_group_repository(connection) -> AchievementGroupRepository:
    return AchievementGroupRepository(connection)


@pytest.fixture
def achievement_progress_repository(connection) -> AchievementProgressRepository:
    return AchievementProgressRepository(connection)


@pytest.fixture
def play_activity_repository(connection) -> PlayActivityRepository:
    return PlayActivityRepository(connection)


@pytest.fixture
def import_service(
    game_repository,
    game_release_repository,
    external_identifier_repository,
    source_game_mapping_repository,
    achievement_repository,
    achievement_group_repository,
    achievement_progress_repository,
    play_activity_repository,
) -> PlaystationImportService:
    return PlaystationImportService(
        game_repository=game_repository,
        game_release_repository=game_release_repository,
        external_identifier_repository=external_identifier_repository,
        source_game_mapping_repository=source_game_mapping_repository,
        achievement_repository=achievement_repository,
        achievement_group_repository=achievement_group_repository,
        achievement_progress_repository=achievement_progress_repository,
        play_activity_repository=play_activity_repository,
    )


@pytest.fixture
def mapped_game() -> Game:
    return Game(
        id="minecraft",
        name="Minecraft",
        sort_name="minecraft",
    )


@pytest.fixture
def mapped_identifier() -> ExternalIdentifier:
    return ExternalIdentifier(
        service="playstation_network",
        identifier_type="title_id",
        value="CUSA00265_00",
    )


@pytest.fixture
def mapped_release(mapped_identifier) -> GameRelease:
    return GameRelease(
        id="minecraft-ps4",
        game_id="minecraft",
        platform_id="ps4",
        name="Minecraft: PlayStation 4 Edition",
        external_identifiers=[mapped_identifier],
    )


@pytest.fixture
def mapped_mapping() -> SourceGameMapping:
    return SourceGameMapping(
        source="playstation_title",
        source_id="CUSA00265_00",
        game_release_id="minecraft-ps4",
        match_method="external_id",
        confidence=1.0,
    )


@pytest.fixture
def mapped_achievement_group(mapped_release) -> AchievementGroup:
    return AchievementGroup(
        id="minecraft-ps4-achievements-group-default",
        game_release_id=mapped_release.id,
        external_group_id="default",
        name="Base Game",
    )


@pytest.fixture
def mapped_achievement(
    mapped_release,
    mapped_achievement_group,
) -> Achievement:
    return Achievement(
        id="minecraft-ps4-achievement-1",
        game_release_id=mapped_release.id,
        group_id=mapped_achievement_group.id,
        external_id="1",
        name="Taking Inventory",
        description="Open your inventory.",
        hidden=False,
        achievement_type="bronze",
        global_unlock_percentage=80.5,
    )


@pytest.fixture
def mapped_achievement_progress(mapped_achievement) -> AchievementProgress:
    return AchievementProgress(
        achievement_id=mapped_achievement.id,
        account_id="psn:123456789",
        unlocked=True,
        progress=100,
        progress_percentage=100,
    )


@pytest.fixture
def mapped_activity(mapped_release) -> PlayActivity:
    return PlayActivity(
        id="ps-activity:CUSA00265_00",
        account_id="psn:123456789",
        game_release_id=mapped_release.id,
        playtime_seconds=7200,
        play_count=4,
        source="PlayStation",
    )


@pytest.fixture
def mapped_data(
    mapped_game,
    mapped_release,
    mapped_mapping,
    mapped_achievement_group,
    mapped_achievement,
    mapped_achievement_progress,
    mapped_activity,
) -> PlayStationMappedData:
    return PlayStationMappedData(
        games=[mapped_game],
        releases=[mapped_release],
        mappings=[mapped_mapping],
        achievement_groups=[mapped_achievement_group],
        achievements=[mapped_achievement],
        achievement_progress=[mapped_achievement_progress],
        activities=[mapped_activity],
    )


def test_importing_mapped_data_persists_catalogue_records(
    import_service,
    game_repository,
    game_release_repository,
    external_identifier_repository,
    source_game_mapping_repository,
    achievement_group_repository,
    achievement_repository,
    achievement_progress_repository,
    play_activity_repository,
    mapped_data,
    mapped_game,
    mapped_release,
    mapped_identifier,
    mapped_mapping,
    mapped_achievement_group,
    mapped_achievement,
    mapped_achievement_progress,
    mapped_activity,
):
    import_service.import_data(mapped_data)

    assert game_repository.get(mapped_game.id) == mapped_game
    assert game_release_repository.get(mapped_release.id) == mapped_release
    assert external_identifier_repository.get_all_for_release(mapped_release.id) == [
        mapped_identifier
    ]
    assert (
        source_game_mapping_repository.get(
            mapped_mapping.source,
            mapped_mapping.source_id,
        )
        == mapped_mapping
    )
    assert achievement_group_repository.get(mapped_achievement_group.id) == (
        mapped_achievement_group
    )
    assert achievement_repository.get(mapped_achievement.id) == mapped_achievement
    assert (
        achievement_progress_repository.get(
            mapped_achievement_progress.achievement_id,
            mapped_achievement_progress.account_id,
        )
        == mapped_achievement_progress
    )
    assert (
        play_activity_repository.get(
            mapped_activity.game_release_id,
            mapped_activity.account_id,
        )
        == mapped_activity
    )


def test_importing_mapped_data_upserts_existing_catalogue_records(
    connection,
    import_service,
    game_repository,
    game_release_repository,
    source_game_mapping_repository,
    mapped_data,
    mapped_game,
    mapped_release,
    mapped_mapping,
):
    existing_game = mapped_game.model_copy(update={"name": "Old Minecraft"})
    existing_release = mapped_release.model_copy(
        update={
            "name": "Old Minecraft Release",
            "external_identifiers": [],
        }
    )
    existing_mapping = mapped_mapping.model_copy(
        update={
            "match_method": "manual",
            "confidence": 0.5,
        }
    )
    game_repository.upsert(existing_game)
    game_release_repository.upsert(existing_release)
    source_game_mapping_repository.upsert(existing_mapping)

    import_service.import_data(mapped_data)

    assert game_repository.get(mapped_game.id) == mapped_game
    assert game_release_repository.get(mapped_release.id) == mapped_release
    assert (
        source_game_mapping_repository.get(
            mapped_mapping.source,
            mapped_mapping.source_id,
        )
        == mapped_mapping
    )

    for table in (
        "game",
        "game_release",
        "source_game_mapping",
        "achievement_group",
        "achievement",
        "achievement_progress",
        "play_activity",
    ):
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        assert count == 1


def test_importing_same_mapped_data_twice_is_idempotent(
    connection,
    import_service,
    game_repository,
    game_release_repository,
    source_game_mapping_repository,
    mapped_data,
):
    import_service.import_data(mapped_data)
    state_after_first_import = (
        game_repository.get_all(),
        game_release_repository.get_all(),
        source_game_mapping_repository.get_all(),
    )

    import_service.import_data(mapped_data)
    state_after_second_import = (
        game_repository.get_all(),
        game_release_repository.get_all(),
        source_game_mapping_repository.get_all(),
    )

    assert state_after_second_import == state_after_first_import

    for table in (
        "game",
        "game_release",
        "external_identifier",
        "source_game_mapping",
        "achievement_group",
        "achievement",
        "achievement_progress",
        "play_activity",
    ):
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        assert count == 1
