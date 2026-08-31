import sqlite3

from game_vault.models.mapping import SourceGameMapping


class SourceGameMappingRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def get(self, source: str, source_id: str) -> SourceGameMapping | None:
        row = self.connection.execute(
            """
            SELECT source,
                   source_id,
                   game_release_id,
                   match_method,
                   confidence
            FROM source_game_mapping
            WHERE source_id = ?
            AND source = ?
            """,
            (source_id, source),
        ).fetchone()

        if row is None:
            return None

        return SourceGameMapping.model_validate(dict(row))

    def get_by_game_release_id(self, game_release_id: str) -> list[SourceGameMapping]:
        rows = self.connection.execute(
            """
            SELECT source,
                   source_id,
                   game_release_id,
                   match_method,
                   confidence
            FROM source_game_mapping
            WHERE game_release_id = ?
            """,
            (game_release_id,),
        ).fetchall()

        return [SourceGameMapping.model_validate(dict(row)) for row in rows]

    def get_all(self) -> list[SourceGameMapping]:
        rows = self.connection.execute(
            """
            SELECT source,
                   source_id,
                   game_release_id,
                   match_method,
                   confidence
            FROM source_game_mapping
            """
        ).fetchall()

        return [SourceGameMapping.model_validate(dict(row)) for row in rows]

    def upsert(self, source_mapping: SourceGameMapping) -> None:
        self.connection.execute(
            """
            INSERT INTO source_game_mapping (source,
                                             source_id,
                                             game_release_id,
                                             match_method,
                                             confidence)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(source, source_id) DO
            UPDATE SET
                game_release_id = excluded.game_release_id,
                match_method = excluded.match_method,
                confidence = excluded.confidence
            """,
            (
                source_mapping.source,
                source_mapping.source_id,
                source_mapping.game_release_id,
                source_mapping.match_method,
                source_mapping.confidence,
            ),
        )

        self.connection.commit()

    def delete(self, source: str, source_id: str) -> bool:
        cursor = self.connection.execute(
            """
            DELETE
            FROM source_game_mapping
            WHERE source = ?
            AND source_id = ?
            """,
            (source, source_id),
        )

        self.connection.commit()

        return cursor.rowcount > 0
