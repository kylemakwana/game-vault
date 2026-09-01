import sqlite3

from game_vault.databases.connection import get_connection


def test_get_connection_returns_sqlite_connection():
    connection = get_connection(":memory:")

    try:
        assert isinstance(connection, sqlite3.Connection)
    finally:
        connection.close()


def test_get_connection_sets_row_factory_to_sqlite_row():
    connection = get_connection(":memory:")

    try:
        assert connection.row_factory is sqlite3.Row
    finally:
        connection.close()


def test_connection_returns_rows_accessible_by_column_name():
    connection = get_connection(":memory:")

    try:
        connection.execute(
            """
            CREATE TABLE test (
                id TEXT,
                name TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO test (id, name)
            VALUES (?, ?)
            """,
            ("1", "Test"),
        )

        row = connection.execute(
            """
            SELECT id, name
            FROM test
            """
        ).fetchone()

        assert isinstance(row, sqlite3.Row)

        assert row["id"] == "1"
        assert row["name"] == "Test"

    finally:
        connection.close()


def test_get_connection_enables_foreign_keys():
    connection = get_connection(":memory:")

    try:
        result = connection.execute("PRAGMA foreign_keys").fetchone()

        assert result[0] == 1

    finally:
        connection.close()


def test_get_connection_uses_provided_database_path(
    tmp_path,
):
    database_path = tmp_path / "test.db"

    connection = get_connection(str(database_path))

    try:
        connection.execute(
            """
            CREATE TABLE test (
                id TEXT PRIMARY KEY
            )
            """
        )

        connection.execute(
            """
            INSERT INTO test (id)
            VALUES (?)
            """,
            ("test-id",),
        )

        connection.commit()

    finally:
        connection.close()

    second_connection = get_connection(str(database_path))

    try:
        row = second_connection.execute(
            """
            SELECT id
            FROM test
            """
        ).fetchone()

        assert row["id"] == "test-id"

    finally:
        second_connection.close()


def test_get_connection_uses_game_vault_db_by_default(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    connection = get_connection()

    try:
        assert (tmp_path / "game_vault.db").exists()
    finally:
        connection.close()
