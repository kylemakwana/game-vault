"""Persist and retrieve games from SQLite."""

import sqlite3

from game_vault.models.game import Game


class GameRepository:
    """Provide persistence operations for :class:`~game_vault.models.game.Game`."""

    def __init__(self, connection: sqlite3.Connection):
        """Initialise the repository.

        :param connection: Open SQLite connection containing the Game Vault schema.
        """
        self.connection = connection

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> Game:
        """Convert a database row into a game model.

        :param row: SQLite row containing game columns.
        :return: Validated game model.
        """
        game = dict(row)

        genres = row["genres"]

        game["genres"] = genres.split(", ") if genres else []

        return Game.model_validate(game)

    def get(self, game_id: str) -> Game | None:
        """Return a game by identifier.

        :param game_id: Catalogue game identifier.
        :return: Matching game, or ``None`` when it does not exist.
        """
        row = self.connection.execute(
            """
            SELECT id,
                   name,
                   sort_name,
                   release_date,
                   developer,
                   publisher,
                   genres,
                   image_url
            FROM game
            WHERE id = ?
            """,
            (game_id,),
        ).fetchone()

        if row is None:
            return None

        return self._row_to_game(row)

    def get_all(self) -> list[Game]:
        """Return every stored game.

        :return: Stored games in database order.
        """
        rows = self.connection.execute(
            """
            SELECT id,
                name,
                sort_name,
                release_date,
                developer,
                publisher,
                genres,
                image_url
            FROM game
            """
        ).fetchall()

        return [self._row_to_game(row) for row in rows]

    def upsert(self, game: Game) -> None:
        """Insert a game or update its existing record.

        Existing optional metadata is preserved when the corresponding incoming
        value is ``None``.

        :param game: Game to persist.
        """
        self.connection.execute(
            """
            INSERT INTO game (id,
                              name,
                              sort_name,
                              release_date,
                              developer,
                              publisher,
                              genres,
                              image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO
            UPDATE SET
                name = excluded.name,
                sort_name = excluded.sort_name,
                release_date = COALESCE(excluded.release_date, release_date),
                developer = COALESCE(excluded.developer, developer),
                publisher = COALESCE(excluded.publisher, publisher),
                genres = COALESCE(excluded.genres, genres),
                image_url = COALESCE(excluded.image_url, image_url)
            """,
            (
                game.id,
                game.name,
                game.sort_name,
                game.release_date.isoformat() if game.release_date else None,
                game.developer,
                game.publisher,
                ", ".join(game.genres),
                game.image_url,
            ),
        )

        self.connection.commit()

    def delete(self, game_id: str) -> bool:
        """Delete a game and its dependent records.

        :param game_id: Catalog game identifier.
        :return: ``True`` when a row was deleted, otherwise ``False``.
        """
        cursor = self.connection.execute(
            """DELETE FROM game WHERE id = ?""",
            (game_id,),
        )

        self.connection.commit()

        return cursor.rowcount > 0
