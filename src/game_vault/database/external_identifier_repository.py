"""Persist and retrieve external release identifiers from SQLite."""

import sqlite3

from game_vault.models.platform import ExternalIdentifier


class ExternalIdentifierRepository:
    """Provide persistence operations for external release identifiers."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Initialize the repository.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    def get_all_for_release(
        self,
        game_release_id: str,
    ) -> list[ExternalIdentifier]:
        """Return all external identifiers for a release.

        :param game_release_id: Catalog release identifier.
        :return: External identifiers associated with the release.
        """
        rows = self.connection.execute(
            """
            SELECT
                service,
                identifier_type,
                value
            FROM external_identifier
            WHERE game_release_id = ?
            """,
            (game_release_id,),
        ).fetchall()

        return [ExternalIdentifier.model_validate(dict(row)) for row in rows]

    def insert(
        self,
        game_release_id: str,
        external_identifier: ExternalIdentifier,
        commit: bool = True,
    ) -> None:
        """Insert an external identifier if it is not already stored.

        :param game_release_id: Catalog release identifier.
        :param external_identifier: External identifier to persist.
        :param commit: Whether to commit the transaction immediately.
        :raises sqlite3.IntegrityError: If the release does not exist.
        """
        self.connection.execute(
            """
            INSERT INTO external_identifier (game_release_id,
                                             service,
                                             identifier_type,
                                             value)
            VALUES (?, ?, ?, ?) ON CONFLICT(
                game_release_id,
                service,
                identifier_type,
                value
            )
            DO NOTHING
            """,
            (
                game_release_id,
                external_identifier.service,
                external_identifier.identifier_type,
                external_identifier.value,
            ),
        )

        if commit:
            self.connection.commit()

    def delete(
        self,
        game_release_id: str,
        external_identifier: ExternalIdentifier,
    ) -> bool:
        """Delete one external identifier from a release.

        :param game_release_id: Catalog release identifier.
        :param external_identifier: Exact external identifier to delete.
        :return: ``True`` when a row was deleted, otherwise ``False``.
        """
        cursor = self.connection.execute(
            """
            DELETE FROM external_identifier 
            WHERE game_release_id = ?
            AND service = ?
            AND identifier_type = ?
            AND value = ?
            """,
            (
                game_release_id,
                external_identifier.service,
                external_identifier.identifier_type,
                external_identifier.value,
            ),
        )

        self.connection.commit()

        return cursor.rowcount > 0
