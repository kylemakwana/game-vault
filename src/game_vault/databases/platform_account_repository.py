"""Persist and retrieve play activity from SQLite."""

import sqlite3

from game_vault.config import PlatformEnum
from game_vault.models.platform import PlatformAccount


class PlatformAccountRepository:
    """Provide persistence operations for
    :class: `~game_vault.models.platform.PlatformAccount`.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Initialise the repository.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    def get_by_id_and_platform(
        self, account_id: str, platform: PlatformEnum
    ) -> PlatformAccount | None:
        """
        Retrieve a platform account from the database.

        :param platform: The ``platformEnum`` to retrieve the ``PlatformAccount`` for.
        :param account_id: The account ID.
        :return: PlatformAccount object for the account.
        """
        row = self.connection.execute(
            """
            SELECT service_id,
                   username,
                   external_account_id,
                   avatar_url

            FROM platform_account
            WHERE external_account_id = ?
            AND service_id = ?
            """,
            (account_id, platform.value),
        ).fetchone()

        if row is None:
            return None

        return PlatformAccount.model_validate(dict(row))

    def get_by_username_and_platform(
        self, username: str, platform: PlatformEnum
    ) -> PlatformAccount | None:
        """
        Retrieve a platform account from the database.

        :param username: The username to retrieve the ``PlatformAccount`` for.
        :param platform: The ``PlatformEnum`` to retrieve the ``PlatformAccount`` for.
        :return: The ``PlatformAccount`` object for the account or ``None`` otherwise.
        """
        row = self.connection.execute(
            """
            SELECT service_id,
                   username,
                   external_account_id,
                   avatar_url
           FROM platform_account
            WHERE username = ?
            AND service_id = ?
            """,
            (username, platform.value),
        ).fetchone()

        if row is None:
            return None

        return PlatformAccount.model_validate(dict(row))

    def get_all_by_username(self, username: str) -> list[PlatformAccount]:
        """
        Retrieve all platform accounts from the database with the given username.

        :param username: The username to retrieve the ``PlatformAccount`` for.
        :return: A list of ``PlatformAccount`` objects for the account.
        """
        rows = self.connection.execute(
            """
            SELECT service_id,
                   username,
                   external_account_id,
                   avatar_url
            FROM platform_account
            WHERE username = ?
            """,
            (username,),
        ).fetchall()

        return [PlatformAccount.model_validate(dict(row)) for row in rows]

    def get_all_by_id(self, account_id: str) -> list[PlatformAccount]:
        """
        Retrieve all platform accounts for the given account ID.

        :param account_id: The account ID.
        :return: `list` of `PlatformAccount` objects.
        """
        rows = self.connection.execute(
            """
            SELECT service_id,
                   username,
                   external_account_id,
                   avatar_url
            FROM platform_account
            WHERE external_account_id = ?
            """,
            (account_id,),
        ).fetchall()

        return [PlatformAccount.model_validate(dict(row)) for row in rows]

    def upsert(self, platform_account: PlatformAccount | None) -> None:
        """
        Add or update a platform account to the database.

        :param platform_account: The platform account to add.
        """
        self.connection.execute(
            """
            INSERT INTO platform_account (service_id,
                                       username,
                                       external_account_id,
                                       avatar_url)
            VALUES (?, ?, ?, ?) ON CONFLICT (service_id, external_account_id) DO
            UPDATE SET
                username = EXCLUDED.username,
                avatar_url = EXCLUDED.avatar_url
            """,
            (
                platform_account.service_id.value,
                platform_account.username,
                platform_account.external_account_id,
                platform_account.avatar_url,
            ),
        )

        self.connection.commit()

    def delete(self, platform: PlatformEnum, account_id: str) -> bool:
        """
        Delete a ``PlatformAccount`` object from the database.

        :param platform: The ``PlatformEnum`` to delete the ``PlatformAccount`` for.
        :param account_id: The account ID to delete the ``PlatformAccount`` for.
        :return: `True` if the platform account was deleted, `False` otherwise.
        """
        cursor = self.connection.execute(
            """
            DELETE
            FROM platform_account
            WHERE service_id = ?
            AND external_account_id = ?""",
            (platform.value, account_id),
        )

        self.connection.commit()

        return cursor.rowcount > 0
