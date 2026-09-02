from game_vault.databases.achievement_repository import AchievementRepository


def test_get_returns_achievement(
    db_connection,
    stored_achievement,
):
    repository = AchievementRepository(db_connection)

    result = repository.get(stored_achievement.id)

    assert result == stored_achievement


def test_get_returns_none_when_achievement_does_not_exist(db_connection):
    repository = AchievementRepository(db_connection)

    result = repository.get("does-not-exist")

    assert result is None


def test_get_all_returns_all_achievements(
    db_connection,
    achievement,
):
    repository = AchievementRepository(db_connection)

    repository.upsert(achievement)

    result = repository.get_all()

    assert result == [achievement]


def test_get_all_returns_empty_list_when_no_achievements_exist(db_connection):
    repository = AchievementRepository(db_connection)

    result = repository.get_all()

    assert result == []


def test_upsert_inserts_achievement(
    db_connection,
    achievement,
):
    repository = AchievementRepository(db_connection)

    repository.upsert(achievement)

    row = db_connection.execute(
        """
        SELECT *
        FROM achievement
        WHERE id = ?
        """,
        (achievement.id,),
    ).fetchone()

    assert row is not None
    assert row["id"] == achievement.id
    assert row["game_release_id"] == achievement.game_release_id
    assert row["group_id"] == achievement.group_id
    assert row["external_id"] == achievement.external_id
    assert row["name"] == achievement.name
    assert row["global_unlock_percentage"] == achievement.global_unlock_percentage


def test_upsert_keeps_highest_global_unlock_percentage(
    db_connection,
    achievement,
):
    repository = AchievementRepository(db_connection)

    repository.upsert(achievement)
    repository.upsert(achievement.model_copy(update={"global_unlock_percentage": 25.0}))

    result = repository.get(achievement.id)

    assert result is not None
    assert result.global_unlock_percentage == 80.5


def test_upsert_commits_transaction(
    db_connection,
    achievement,
):
    repository = AchievementRepository(db_connection)

    repository.upsert(achievement)

    assert db_connection.in_transaction is False


def test_delete_removes_existing_achievement(
    db_connection,
    stored_achievement,
):
    repository = AchievementRepository(db_connection)

    result = repository.delete(stored_achievement.id)

    assert result is True
    assert repository.get(stored_achievement.id) is None


def test_delete_returns_false_when_achievement_does_not_exist(db_connection):
    repository = AchievementRepository(db_connection)

    result = repository.delete("does-not-exist")

    assert result is False
