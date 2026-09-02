from game_vault.databases.play_activity_repository import PlayActivityRepository


def test_get_returns_play_activity(
    db_connection,
    play_activity,
):
    repository = PlayActivityRepository(db_connection)

    repository.upsert(play_activity)

    result = repository.get(
        play_activity.game_release_id,
        play_activity.account_id,
    )

    assert result == play_activity


def test_get_returns_none_when_play_activity_does_not_exist(db_connection):
    repository = PlayActivityRepository(db_connection)

    result = repository.get("does-not-exist", "psn:missing")

    assert result is None


def test_get_all_returns_all_play_activities_for_account(
    db_connection,
    play_activity,
):
    repository = PlayActivityRepository(db_connection)

    repository.upsert(play_activity)

    result = repository.get_all(play_activity.account_id)

    assert result == [play_activity]


def test_get_all_returns_empty_list_when_account_has_no_play_activities(db_connection):
    repository = PlayActivityRepository(db_connection)

    result = repository.get_all("psn:missing")

    assert result == []


def test_upsert_updates_existing_play_activity(
    db_connection,
    play_activity,
):
    repository = PlayActivityRepository(db_connection)

    repository.upsert(play_activity)
    updated_activity = play_activity.model_copy(
        update={
            "playtime_seconds": 9000,
            "play_count": 5,
        }
    )
    repository.upsert(updated_activity)

    result = repository.get(
        play_activity.game_release_id,
        play_activity.account_id,
    )

    assert result == updated_activity


def test_upsert_commits_transaction(
    db_connection,
    play_activity,
):
    repository = PlayActivityRepository(db_connection)

    repository.upsert(play_activity)

    assert db_connection.in_transaction is False


def test_delete_removes_existing_play_activity(
    db_connection,
    play_activity,
):
    repository = PlayActivityRepository(db_connection)
    repository.upsert(play_activity)

    result = repository.delete(
        play_activity.game_release_id,
        play_activity.account_id,
    )

    assert result is True
    assert (
        repository.get(
            play_activity.game_release_id,
            play_activity.account_id,
        )
        is None
    )


def test_delete_returns_false_when_play_activity_does_not_exist(db_connection):
    repository = PlayActivityRepository(db_connection)

    result = repository.delete("does-not-exist", "psn:missing")

    assert result is False
