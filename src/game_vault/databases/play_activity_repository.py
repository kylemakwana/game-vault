"""Persist and retrieve play activity from SQLite."""

import sqlite3

from game_vault.models.activity import PlayActivity


class PlayActivityRepository:
    """Provide persistence operations for
    :class: `~game_vault.models.activity.PlayActivity`.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Initialise the repository.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    def get(self, game_release_id: str, account_id: str) -> PlayActivity | None:
        """
        Retrieve a play activity from the database.

        :param game_release_id: The ID for the game release.
        :param account_id: The account ID.
        :return: PlayActivity object for the account and game release.
        """
        row = self.connection.execute(
            """
            SELECT account_id,
            game_release_id,
            playtime_seconds,
            play_count,
            first_played_at,
            last_played_at,
            source
            
            FROM play_activity
                WHERE game_release_id = ?
                AND account_id = ?
            """,
            (game_release_id, account_id),
        ).fetchone()

        if row is None:
            return None

        return PlayActivity.model_validate(dict(row))

    def get_all(self, account_id: str) -> list[PlayActivity]:
        """
        Retrieve all play activities for the given account.

        :param account_id: The account ID.
        :return: `list` of `PlayActivity` objects.
        """
        rows = self.connection.execute(
            """
            SELECT account_id,
            game_release_id,
            playtime_seconds,
            play_count,
            first_played_at,
            last_played_at,
            source
            FROM play_activity
                WHERE account_id = ?
            """,
            (account_id,),
        ).fetchall()

        return [PlayActivity.model_validate(dict(row)) for row in rows]

    def upsert(self, play_activity: PlayActivity) -> None:
        """
        Add or update a play activity to the database.

        :param play_activity: The play activity to add.
        """
        self.connection.execute(
            """
            INSERT INTO play_activity (account_id,
                                       game_release_id,
                                       playtime_seconds,
                                       play_count,
                                       first_played_at,
                                       last_played_at,
                                       source)
            VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (account_id, game_release_id) DO
            UPDATE SET
                playtime_seconds = EXCLUDED.playtime_seconds,
                play_count = EXCLUDED.play_count,
                first_played_at = EXCLUDED.first_played_at,
                last_played_at = EXCLUDED.last_played_at,
                source = EXCLUDED.source
            """,
            (
                play_activity.account_id,
                play_activity.game_release_id,
                play_activity.playtime_seconds,
                play_activity.play_count,
                play_activity.first_played_at,
                play_activity.last_played_at,
                play_activity.source,
            ),
        )

        self.connection.commit()

    def delete(self, game_release_id: str, account_id: str) -> bool:
        """
        Delete a play activity from the database.

        :param game_release_id: The ID for the game release.
        :param account_id: The account ID.
        :return: `True` if the play activity was deleted, `False` otherwise.
        """
        cursor = self.connection.execute(
            """DELETE FROM play_activity
            WHERE game_release_id = ? AND account_id = ?""",
            (game_release_id, account_id),
        )

        self.connection.commit()

        return cursor.rowcount > 0
