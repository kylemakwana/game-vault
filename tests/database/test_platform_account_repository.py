import pytest

from game_vault.config import PlatformEnum
from game_vault.databases.platform_account_repository import PlatformAccountRepository
from game_vault.models.platform import PlatformAccount


@pytest.fixture
def repository(db_connection):
    return PlatformAccountRepository(db_connection)


@pytest.fixture
def platform_account():
    return PlatformAccount(
        service_id=PlatformEnum.PLAYSTATION,
        username="TestUser",
        external_account_id="123456789",
        avatar_url="https://example.com/avatar.png",
    )


@pytest.fixture
def stored_accounts(db_connection, platform_account):
    accounts = [
        platform_account,
        platform_account.model_copy(
            update={"service_id": PlatformEnum.STEAM, "avatar_url": None}
        ),
        platform_account.model_copy(
            update={"username": "OtherUser", "external_account_id": "987654321"}
        ),
    ]
    db_connection.executemany(
        """
        INSERT INTO platform_account (
            service_id, username, external_account_id, avatar_url
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                account.service_id.value,
                account.username,
                account.external_account_id,
                account.avatar_url,
            )
            for account in accounts
        ],
    )
    db_connection.commit()
    return accounts


@pytest.mark.parametrize(
    ("method", "field"),
    [
        ("get_by_id_and_platform", "external_account_id"),
        ("get_by_username_and_platform", "username"),
    ],
)
@pytest.mark.parametrize("account_index", [0, 1, 2])
def test_lookup_returns_account_for_matching_platform(
    repository, stored_accounts, method, field, account_index
):
    account = stored_accounts[account_index]

    result = getattr(repository, method)(getattr(account, field), account.service_id)

    assert result == account
    assert result.service_id is account.service_id


@pytest.mark.parametrize(
    ("method", "value", "platform"),
    [
        ("get_by_id_and_platform", "missing", PlatformEnum.PLAYSTATION),
        ("get_by_id_and_platform", "987654321", PlatformEnum.STEAM),
        ("get_by_username_and_platform", "missing", PlatformEnum.PLAYSTATION),
        ("get_by_username_and_platform", "OtherUser", PlatformEnum.STEAM),
    ],
)
def test_lookup_returns_none_when_no_account_matches(
    repository, stored_accounts, method, value, platform
):
    assert getattr(repository, method)(value, platform) is None


@pytest.mark.parametrize(
    ("method", "value"),
    [("get_all_by_username", "TestUser"), ("get_all_by_id", "123456789")],
)
def test_get_all_returns_only_matching_accounts_across_platforms(
    repository, stored_accounts, method, value
):
    result = getattr(repository, method)(value)

    assert len(result) == 2
    assert stored_accounts[0] in result
    assert stored_accounts[1] in result


@pytest.mark.parametrize("method", ["get_all_by_username", "get_all_by_id"])
def test_get_all_returns_empty_list_when_no_account_matches(
    repository, stored_accounts, method
):
    assert getattr(repository, method)("missing") == []


@pytest.mark.parametrize("avatar_url", [None, "https://example.com/avatar.png"])
def test_upsert_inserts_account_and_commits(
    db_connection, repository, platform_account, avatar_url
):
    account = platform_account.model_copy(update={"avatar_url": avatar_url})

    repository.upsert(account)

    row = db_connection.execute("SELECT * FROM platform_account").fetchone()
    assert dict(row) == account.model_dump(mode="json")
    assert db_connection.in_transaction is False


@pytest.mark.parametrize("avatar_url", [None, "https://example.com/updated-avatar.png"])
def test_upsert_updates_only_matching_account_and_commits(
    db_connection, repository, stored_accounts, avatar_url
):
    updated_account = stored_accounts[0].model_copy(
        update={"username": "RenamedUser", "avatar_url": avatar_url}
    )

    repository.upsert(updated_account)

    rows = db_connection.execute("SELECT * FROM platform_account").fetchall()
    accounts = [PlatformAccount.model_validate(dict(row)) for row in rows]
    assert len(accounts) == 3
    assert updated_account in accounts
    assert stored_accounts[1] in accounts
    assert stored_accounts[2] in accounts
    assert db_connection.in_transaction is False


def test_upsert_preserves_accounts_with_same_id_on_different_platforms(
    db_connection, repository, platform_account
):
    steam_account = platform_account.model_copy(
        update={"service_id": PlatformEnum.STEAM, "username": "SteamUser"}
    )

    repository.upsert(platform_account)
    repository.upsert(steam_account)

    rows = db_connection.execute("SELECT * FROM platform_account").fetchall()
    accounts = [PlatformAccount.model_validate(dict(row)) for row in rows]
    assert len(accounts) == 2
    assert platform_account in accounts
    assert steam_account in accounts


def test_delete_removes_only_matching_account_and_commits(
    db_connection, repository, stored_accounts
):
    account = stored_accounts[0]

    result = repository.delete(account.service_id, account.external_account_id)

    assert result is True
    rows = db_connection.execute("SELECT * FROM platform_account").fetchall()
    accounts = [PlatformAccount.model_validate(dict(row)) for row in rows]
    assert len(accounts) == 2
    assert stored_accounts[1] in accounts
    assert stored_accounts[2] in accounts
    assert db_connection.in_transaction is False


@pytest.mark.parametrize(
    ("platform", "account_id"),
    [(PlatformEnum.PLAYSTATION, "missing"), (PlatformEnum.STEAM, "987654321")],
)
def test_delete_returns_false_and_preserves_accounts_when_no_account_matches(
    db_connection, repository, stored_accounts, platform, account_id
):
    result = repository.delete(platform, account_id)

    assert result is False
    rows = db_connection.execute("SELECT * FROM platform_account").fetchall()
    accounts = [PlatformAccount.model_validate(dict(row)) for row in rows]
    assert len(accounts) == len(stored_accounts)
    assert all(account in accounts for account in stored_accounts)
    assert db_connection.in_transaction is False
