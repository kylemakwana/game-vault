import sqlite3


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE game (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sort_name TEXT NOT NULL,
            release_date TEXT,
            developer TEXT,
            publisher TEXT,
            genres TEXT,
            image_url TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE game_release (
            id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            platform_id TEXT NOT NULL,
            name TEXT NOT NULL,
            release_date TEXT,
            image_url TEXT,

            FOREIGN KEY (game_id)
                REFERENCES game(id)
                ON DELETE CASCADE
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE external_identifier (
            game_release_id TEXT NOT NULL,
            service TEXT NOT NULL,
            identifier_type TEXT NOT NULL,
            value TEXT NOT NULL,

            PRIMARY KEY (
                game_release_id,
                service,
                identifier_type,
                value
            ),

            FOREIGN KEY (game_release_id)
                REFERENCES game_release(id)
                ON DELETE CASCADE
        )
        """
    )


def drop_tables(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS game_release")
    connection.execute("DROP TABLE IF EXISTS game")
    connection.execute("DROP TABLE IF EXISTS external_identifier")
