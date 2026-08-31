"""Persist and retrieve platform-specific game releases from SQLite."""

import sqlite3

from game_vault.database.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.models.game import GameRelease


class GameReleaseRepository:
    """Provide persistence operations for game releases."""

    def __init__(self, connection: sqlite3.Connection):
        """Initialize the repository.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    def get(self, game_release_id: str) -> GameRelease | None:
        """Return a release and its external identifiers.

        :param game_release_id: Catalog release identifier.
        :return: Matching release, or ``None`` when it does not exist.
        """
        row = self.connection.execute(
            """
            SELECT id,
                   game_id,
                   platform_id,
                   name,
                   release_date,
                   image_url
            FROM game_release
            WHERE id = ?
            """,
            (game_release_id,),
        ).fetchone()

        if row is None:
            return None

        external_identifier_repo = ExternalIdentifierRepository(self.connection)
        ex_ids = external_identifier_repo.get_all_for_release(game_release_id)

        game_release = dict(row)
        game_release["external_identifiers"] = ex_ids

        return GameRelease.model_validate(game_release)

    def get_by_game_id(self, game_id: str) -> list[GameRelease]:
        """Return all releases belonging to a game.

        :param game_id: Catalog game identifier.
        :return: Matching releases with their external identifiers.
        """
        rows = self.connection.execute(
            """
            SELECT id,
                   game_id,
                   platform_id,
                   name,
                   release_date,
                   image_url
            FROM game_release
            WHERE game_id = ?
            """,
            (game_id,),
        ).fetchall()

        external_identifier_repo = ExternalIdentifierRepository(self.connection)
        releases = []
        for row in rows:
            release = dict(row)
            ex_ids = external_identifier_repo.get_all_for_release(release["id"])
            release["external_identifiers"] = ex_ids
            releases.append(GameRelease.model_validate(release))

        return releases

    def get_all(self) -> list[GameRelease]:
        """Return every stored release with its external identifiers.

        :return: Stored releases in database order.
        """
        rows = self.connection.execute(
            """
            SELECT id,
                   game_id,
                   platform_id,
                   name,
                   release_date,
                   image_url
            FROM game_release
            """
        ).fetchall()

        external_identifier_repo = ExternalIdentifierRepository(self.connection)

        releases = []

        for row in rows:
            release = dict(row)

            release["external_identifiers"] = (
                external_identifier_repo.get_all_for_release(row["id"])
            )

            releases.append(GameRelease.model_validate(release))

        return releases

    def upsert(self, game_release: GameRelease) -> None:
        """Insert a release or update it and add its external identifiers.

        Existing optional metadata is preserved when the corresponding incoming
        value is ``None``.

        :param game_release: Release to persist.
        :raises sqlite3.IntegrityError: If the release references an unknown game.
        """
        self.connection.execute(
            """
            INSERT INTO game_release (id,
                                      game_id,
                                      platform_id,
                                      name,
                                      release_date,
                                      image_url)
            VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO
            UPDATE SET
                name = excluded.name,
                release_date = COALESCE (
                excluded.release_date,
                game_release.release_date
                ),
                image_url = COALESCE (
                excluded.image_url,
                game_release.image_url
                )
            """,
            (
                game_release.id,
                game_release.game_id,
                game_release.platform_id,
                game_release.name,
                (
                    game_release.release_date.isoformat()
                    if game_release.release_date
                    else None
                ),
                game_release.image_url,
            ),
        )

        ex_id_repo = ExternalIdentifierRepository(self.connection)

        for external_identifier in game_release.external_identifiers:
            ex_id_repo.insert(
                game_release.id,
                external_identifier,
                commit=False,
            )

        self.connection.commit()

    def delete(self, game_release_id: str) -> bool:
        """Delete a release and its dependent records.

        :param game_release_id: Catalog release identifier.
        :return: ``True`` when a row was deleted, otherwise ``False``.
        """
        cursor = self.connection.execute(
            """
            DELETE
            FROM game_release
            WHERE id = ?
            """,
            (game_release_id,),
        )

        self.connection.commit()

        return cursor.rowcount > 0
