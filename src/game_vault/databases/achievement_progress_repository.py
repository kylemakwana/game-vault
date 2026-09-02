"""Persist and retrieve achievement progress."""

import sqlite3

from game_vault.models.achievement import AchievementProgress


class AchievementProgressRepository:
    """Provide persistence operations for
    :class:`~game_vault.models.achievement.AchievementProgress`.
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialise the :class:`AchievementProgressRepository`.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    def get(
        self,
        achievement_id: str,
        account_id: str,
    ) -> AchievementProgress | None:
        """Retrieve an achievement progress by the achievement ID.

        :param achievement_id: ID of achievement.
        :param account_id: ID of account.
        :return: Achievement progress or ``None`` if not found.
        """
        row = self.connection.execute(
            """SELECT achievement_id,
                          account_id,
                          unlocked,
                          unlocked_at,
                          progress,
                          progress_percentage,
                          progressed_at
                FROM achievement_progress 
                WHERE achievement_id = ?
                AND account_id = ?
                """,
            (achievement_id, account_id),
        ).fetchone()

        if row is None:
            return None

        return AchievementProgress.model_validate(dict(row))

    def get_all(self) -> list[AchievementProgress]:
        """Retrieve all achievement progress.

        :return: List of achievement progress.
        """
        rows = self.connection.execute(
            """SELECT achievement_id,
                          account_id,
                          unlocked,
                          unlocked_at,
                          progress,
                          progress_percentage,
                          progressed_at
            FROM achievement_progress
            """
        ).fetchall()

        return [AchievementProgress.model_validate(dict(row)) for row in rows]

    def upsert(self, achievement_progress: AchievementProgress) -> None:
        """Insert or update an achievement's progress.

        :param achievement_progress: Achievement progress.
        """
        self.connection.execute(
            """
            INSERT INTO achievement_progress (
                achievement_id,
                account_id,
                unlocked,
                unlocked_at,
                progress,
                progress_percentage,
                progressed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (achievement_id, account_id) DO
            UPDATE SET
                unlocked = excluded.unlocked,
                unlocked_at = excluded.unlocked_at,
                progress = excluded.progress,
                progress_percentage = excluded.progress_percentage,
                progressed_at = excluded.progressed_at
            """,
            (
                achievement_progress.achievement_id,
                achievement_progress.account_id,
                achievement_progress.unlocked,
                achievement_progress.unlocked_at,
                achievement_progress.progress,
                achievement_progress.progress_percentage,
                achievement_progress.progressed_at,
            ),
        )

        self.connection.commit()

    def delete(
        self,
        achievement_id: str,
        account_id: str,
    ) -> bool:
        """Delete an achievement progress by the achievement ID.

        :param achievement_id: ID of achievement.
        :param account_id: ID of account.
        :return: ``True`` when a row is deleted, otherwise ``False``.
        """
        cursor = self.connection.execute(
            """
            DELETE FROM achievement_progress
            WHERE achievement_id = ?
            AND account_id = ?
            """,
            (achievement_id, account_id),
        )

        self.connection.commit()

        return cursor.rowcount > 0
