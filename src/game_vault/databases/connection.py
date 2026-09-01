"""Create configured SQLite database connections."""

import sqlite3


def get_connection(database: str = "game_vault.db") -> sqlite3.Connection:
    """Open a SQLite connection configured for Game Vault.

    The returned connection exposes rows by column name and enforces foreign-key
    constraints.

    :param database: Database filename or SQLite connection target.
    :return: Configured SQLite connection.
    """
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection
