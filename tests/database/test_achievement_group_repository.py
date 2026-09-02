from game_vault.databases.achievement_group_repository import (
    AchievementGroupRepository,
)


def test_get_returns_achievement_group(
    db_connection,
    stored_achievement_group,
):
    repository = AchievementGroupRepository(db_connection)

    result = repository.get(stored_achievement_group.id)

    assert result == stored_achievement_group


def test_get_returns_none_when_achievement_group_does_not_exist(db_connection):
    repository = AchievementGroupRepository(db_connection)

    result = repository.get("does-not-exist")

    assert result is None


def test_get_all_returns_all_achievement_groups(
    db_connection,
    achievement_group,
):
    repository = AchievementGroupRepository(db_connection)

    repository.insert(achievement_group)

    result = repository.get_all()

    assert result == [achievement_group]


def test_get_all_returns_empty_list_when_no_achievement_groups_exist(db_connection):
    repository = AchievementGroupRepository(db_connection)

    result = repository.get_all()

    assert result == []


def test_insert_ignores_duplicate_achievement_group(
    db_connection,
    achievement_group,
):
    repository = AchievementGroupRepository(db_connection)

    repository.insert(achievement_group)
    repository.insert(achievement_group)

    result = repository.get_all()

    assert result == [achievement_group]


def test_insert_commits_transaction(
    db_connection,
    achievement_group,
):
    repository = AchievementGroupRepository(db_connection)

    repository.insert(achievement_group)

    assert db_connection.in_transaction is False


def test_delete_removes_existing_achievement_group(
    db_connection,
    stored_achievement_group,
):
    repository = AchievementGroupRepository(db_connection)

    result = repository.delete(stored_achievement_group.id)

    assert result is True
    assert repository.get(stored_achievement_group.id) is None


def test_delete_returns_false_when_achievement_group_does_not_exist(db_connection):
    repository = AchievementGroupRepository(db_connection)

    result = repository.delete("does-not-exist")

    assert result is False
