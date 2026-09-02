"""Persist and retrieve achievement groups from SQLite"""

import sqlite3

from game_vault.models.achievement import AchievementGroup


class AchievementGroupRepository:
    """provide persistence operations for
    :class:`~game_vault.models.achievement.AchievementGroup`
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialise the repository.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    def get(self, achievement_group_id: str) -> AchievementGroup | None:
        """Return the achievement group with the given achievement group id.

        :param achievement_group_id: The achievement group id.
        :return: The achievement group or ``None`` if not found.
        """
        row = self.connection.execute(
            """
            SELECT id, game_release_id, external_group_id, name
            FROM achievement_group 
            WHERE id = ?
            """,
            (achievement_group_id,),
        ).fetchone()

        if row is None:
            return None

        return AchievementGroup.model_validate(dict(row))

    def get_all(self) -> list[AchievementGroup]:
        """Return all achievement groups.

        :return: All achievement groups.
        """
        rows = self.connection.execute(
            """
            SELECT id, game_release_id, external_group_id, name
            FROM achievement_group
            """
        ).fetchall()

        return [AchievementGroup.model_validate(dict(row)) for row in rows]

    def insert(self, achievement_group: AchievementGroup) -> None:
        """Insert the achievement group into the database.

        :param achievement_group: The achievement group.
        """
        self.connection.execute(
            """
            INSERT INTO achievement_group (
                id,
                game_release_id, 
                external_group_id, 
                name
            )
            VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING
            """,
            (
                achievement_group.id,
                achievement_group.game_release_id,
                achievement_group.external_group_id,
                achievement_group.name,
            ),
        )

        self.connection.commit()

    def delete(self, achievement_group_id: str) -> bool:
        """Delete the achievement group with the given achievement group id.
        :param achievement_group_id: The achievement group id.

        :return: ``True`` if the achievement group was deleted, ``False`` otherwise.
        """
        cursor = self.connection.execute(
            """DELETE FROM achievement_group WHERE id = ?""", (achievement_group_id,)
        )

        self.connection.commit()

        return cursor.rowcount > 0
