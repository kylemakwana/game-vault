import sqlite3

from game_vault.models.platform import ExternalIdentifier


class ExternalIdentifierRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_all_for_release(
        self,
        game_release_id: str,
    ) -> list[ExternalIdentifier]:
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
