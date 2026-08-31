import sqlite3

from game_vault.models.game import Game


class GameRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> Game:
        game = dict(row)

        genres = row["genres"]

        game["genres"] = genres.split(", ") if genres else []

        return Game.model_validate(game)

    def get(self, game_id: str) -> Game | None:
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
        cursor = self.connection.execute(
            """
            DELETE
            FROM game
            WHERE id = ?
            """,
            (game_id,),
        )

        self.connection.commit()

        return cursor.rowcount > 0
