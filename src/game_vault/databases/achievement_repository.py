"""Persists and retrieves achievements from SQLite."""

import sqlite3

from game_vault.models.achievement import Achievement


class AchievementRepository:
    """
    Provide persistence operations for
    :class:`~game_vault.models.achievement.Achievement`.
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialise the repository.

        :param connection: Open SQLite3 connection containing the Game Vault schema"""
        self.connection = connection

    def get(self, achievement_id: str) -> Achievement | None:
        """Return an achievement by its ID.

        :param achievement_id: ID of achievement.
        :return: Validated achievement model or ``None`` if not found.
        """
        row = self.connection.execute(
            """
            SELECT id,
                   game_release_id,
                   group_id,
                   external_id,
                   name,
                   description,
                   icon_url,
                   hidden,
                   achievement_type,
                   rarity,
                   global_unlock_percentage,
                   progress_target
            FROM achievement
            WHERE id = ?
            """,
            (achievement_id,),
        ).fetchone()

        if row is None:
            return None

        return Achievement.model_validate(dict(row))

    def get_all(self) -> list[Achievement]:
        """Return all achievements.

        :return: List of all achievements.
        """
        rows = self.connection.execute(
            """
            SELECT id,
                   game_release_id,
                   group_id,
                   external_id,
                   name,
                   description,
                   icon_url,
                   hidden,
                   achievement_type,
                   rarity,
                   global_unlock_percentage,
                   progress_target
            FROM achievement
            """
        ).fetchall()

        return [Achievement.model_validate(dict(row)) for row in rows]

    def upsert(self, achievement: Achievement) -> None:
        """Add or update an achievement to the database.

        :param achievement: Achievement to add.
        """
        self.connection.execute(
            """
            INSERT INTO achievement (id,
                                     game_release_id,
                                     group_id,
                                     external_id,
                                     name,
                                     description,
                                     icon_url,
                                     hidden,
                                     achievement_type,
                                     rarity,
                                     global_unlock_percentage,
                                     progress_target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO
            UPDATE SET
                global_unlock_percentage = MAX(
                    excluded.global_unlock_percentage, 
                    global_unlock_percentage
                )
            """,
            (
                achievement.id,
                achievement.game_release_id,
                achievement.group_id,
                achievement.external_id,
                achievement.name,
                achievement.description,
                achievement.icon_url,
                achievement.hidden,
                achievement.achievement_type,
                achievement.rarity,
                achievement.global_unlock_percentage,
                achievement.progress_target,
            ),
        )

        self.connection.commit()

    def delete(self, achievement_id: str) -> bool:
        """
        Delete an achievement by its ID.

        :param achievement_id: ID of achievement.
        :return: ``True`` if the achievement group was deleted, ``False`` otherwise.
        """
        cursor = self.connection.execute(
            """DELETE FROM achievement WHERE id = ?""",
            (achievement_id,),
        )

        self.connection.commit()

        return cursor.rowcount > 0
