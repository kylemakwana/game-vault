"""Create and remove the Game Vault SQLite schema."""

import sqlite3


def create_tables(connection: sqlite3.Connection) -> None:
    """Create all Game Vault database tables.

    :param connection: Open SQLite connection on which to create the schema.
    :raises sqlite3.OperationalError: If a table already exists or SQL execution
        otherwise fails.
    """
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS game (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sort_name TEXT,
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
        CREATE TABLE IF NOT EXISTS game_release (
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
        CREATE TABLE IF NOT EXISTS external_identifier (
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

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source_game_mapping
        (
            source          TEXT NOT NULL,
            source_id       TEXT NOT NULL,
            game_release_id TEXT NOT NULL,
            match_method    TEXT NOT NULL,
            confidence      REAL,

            PRIMARY KEY (
                         source,
                         source_id
                ),

            FOREIGN KEY (game_release_id)
                REFERENCES game_release(id)
                ON DELETE CASCADE
        )
        """
    )


def drop_tables(connection: sqlite3.Connection) -> None:
    """Drop all Game Vault database tables if they exist.

    Tables are removed in dependency order.

    :param connection: Open SQLite connection from which to remove the schema.
    """
    connection.execute("DROP TABLE IF EXISTS source_game_mapping")
    connection.execute("DROP TABLE IF EXISTS external_identifier")
    connection.execute("DROP TABLE IF EXISTS game_release")
    connection.execute("DROP TABLE IF EXISTS game")
