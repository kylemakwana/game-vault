from game_vault.databases.achievement_progress_repository import (
    AchievementProgressRepository,
)


def test_get_returns_achievement_progress(
    db_connection,
    achievement_progress,
):
    repository = AchievementProgressRepository(db_connection)

    repository.upsert(achievement_progress)

    result = repository.get(
        achievement_progress.achievement_id,
        achievement_progress.account_id,
    )

    assert result == achievement_progress


def test_get_returns_none_when_achievement_progress_does_not_exist(db_connection):
    repository = AchievementProgressRepository(db_connection)

    result = repository.get("does-not-exist", "psn:missing")

    assert result is None


def test_get_all_returns_all_achievement_progress(
    db_connection,
    achievement_progress,
):
    repository = AchievementProgressRepository(db_connection)

    repository.upsert(achievement_progress)

    result = repository.get_all()

    assert result == [achievement_progress]


def test_get_all_returns_empty_list_when_no_achievement_progress_exists(db_connection):
    repository = AchievementProgressRepository(db_connection)

    result = repository.get_all()

    assert result == []


def test_upsert_updates_existing_achievement_progress(
    db_connection,
    achievement_progress,
):
    repository = AchievementProgressRepository(db_connection)

    repository.upsert(achievement_progress)
    updated_progress = achievement_progress.model_copy(
        update={
            "unlocked": False,
            "unlocked_at": None,
            "progress": 50,
            "progress_percentage": 50,
        }
    )
    repository.upsert(updated_progress)

    result = repository.get(
        achievement_progress.achievement_id,
        achievement_progress.account_id,
    )

    assert result == updated_progress


def test_upsert_commits_transaction(
    db_connection,
    achievement_progress,
):
    repository = AchievementProgressRepository(db_connection)

    repository.upsert(achievement_progress)

    assert db_connection.in_transaction is False


def test_delete_removes_existing_achievement_progress(
    db_connection,
    achievement_progress,
):
    repository = AchievementProgressRepository(db_connection)
    repository.upsert(achievement_progress)

    result = repository.delete(
        achievement_progress.achievement_id,
        achievement_progress.account_id,
    )

    assert result is True
    assert (
        repository.get(
            achievement_progress.achievement_id,
            achievement_progress.account_id,
        )
        is None
    )


def test_delete_returns_false_when_achievement_progress_does_not_exist(db_connection):
    repository = AchievementProgressRepository(db_connection)

    result = repository.delete("does-not-exist", "psn:missing")

    assert result is False
