import sqlite3

import pytest

from game_vault.database.schema import (
    create_tables,
    drop_tables,
)


def test_create_tables_creates_expected_tables(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    rows = empty_db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    table_names = {row["name"] for row in rows}

    assert table_names == {
        "game",
        "game_release",
        "external_identifier",
        "source_game_mapping",
    }


def test_game_table_has_expected_columns(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    rows = empty_db_connection.execute("PRAGMA table_info(game)").fetchall()

    columns = {row["name"]: row for row in rows}

    assert set(columns) == {
        "id",
        "name",
        "sort_name",
        "release_date",
        "developer",
        "publisher",
        "genres",
        "image_url",
    }


def test_game_table_has_expected_required_columns(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    rows = empty_db_connection.execute("PRAGMA table_info(game)").fetchall()

    columns = {row["name"]: row for row in rows}

    assert columns["id"]["pk"] == 1

    assert columns["name"]["notnull"] == 1

    assert columns["sort_name"]["notnull"] == 0
    assert columns["release_date"]["notnull"] == 0
    assert columns["developer"]["notnull"] == 0
    assert columns["publisher"]["notnull"] == 0
    assert columns["genres"]["notnull"] == 0
    assert columns["image_url"]["notnull"] == 0


def test_game_release_table_has_expected_columns(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    rows = empty_db_connection.execute("PRAGMA table_info(game_release)").fetchall()

    columns = {row["name"]: row for row in rows}

    assert set(columns) == {
        "id",
        "game_id",
        "platform_id",
        "name",
        "release_date",
        "image_url",
    }

    assert columns["id"]["pk"] == 1

    assert columns["game_id"]["notnull"] == 1
    assert columns["platform_id"]["notnull"] == 1
    assert columns["name"]["notnull"] == 1


def test_external_identifier_table_has_expected_columns(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    rows = empty_db_connection.execute(
        "PRAGMA table_info(external_identifier)"
    ).fetchall()

    columns = {row["name"]: row for row in rows}

    assert set(columns) == {
        "game_release_id",
        "service",
        "identifier_type",
        "value",
    }

    assert all(column["notnull"] == 1 for column in columns.values())


def test_game_release_has_foreign_key_to_game(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    foreign_keys = empty_db_connection.execute(
        "PRAGMA foreign_key_list(game_release)"
    ).fetchall()

    assert len(foreign_keys) == 1

    foreign_key = foreign_keys[0]

    assert foreign_key["table"] == "game"
    assert foreign_key["from"] == "game_id"
    assert foreign_key["to"] == "id"
    assert foreign_key["on_delete"] == "CASCADE"


def test_external_identifier_has_foreign_key_to_game_release(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    foreign_keys = empty_db_connection.execute(
        "PRAGMA foreign_key_list(external_identifier)"
    ).fetchall()

    assert len(foreign_keys) == 1

    foreign_key = foreign_keys[0]

    assert foreign_key["table"] == "game_release"
    assert foreign_key["from"] == "game_release_id"
    assert foreign_key["to"] == "id"
    assert foreign_key["on_delete"] == "CASCADE"


def test_game_rejects_missing_required_name(
    db_connection,
):
    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO game (
                id,
                name,
                sort_name
            )
            VALUES (?, ?, ?)
            """,
            (
                "test-game",
                None,
                "test game",
            ),
        )


def test_game_rejects_duplicate_id(
    db_connection,
):
    db_connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name
        )
        VALUES (?, ?, ?)
        """,
        (
            "test-game",
            "Test Game",
            "test game",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO game (
                id,
                name,
                sort_name
            )
            VALUES (?, ?, ?)
            """,
            (
                "test-game",
                "Different Game",
                "different game",
            ),
        )


def test_game_release_requires_existing_game(
    db_connection,
):
    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO game_release (
                id,
                game_id,
                platform_id,
                name
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "test-release",
                "does-not-exist",
                "ps5",
                "Test Game",
            ),
        )


def test_external_identifier_requires_existing_release(
    db_connection,
):
    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO external_identifier (
                game_release_id,
                service,
                identifier_type,
                value
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "does-not-exist",
                "playstation_network",
                "title_id",
                "TEST12345",
            ),
        )


def test_external_identifier_composite_primary_key_prevents_duplicates(
    db_connection,
):
    db_connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name
        )
        VALUES (?, ?, ?)
        """,
        (
            "test-game",
            "Test Game",
            "test game",
        ),
    )

    db_connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "test-release",
            "test-game",
            "ps5",
            "Test Game",
        ),
    )

    identifier = (
        "test-release",
        "playstation_network",
        "title_id",
        "TEST12345",
    )

    db_connection.execute(
        """
        INSERT INTO external_identifier (
            game_release_id,
            service,
            identifier_type,
            value
        )
        VALUES (?, ?, ?, ?)
        """,
        identifier,
    )

    with pytest.raises(sqlite3.IntegrityError):
        db_connection.execute(
            """
            INSERT INTO external_identifier (
                game_release_id,
                service,
                identifier_type,
                value
            )
            VALUES (?, ?, ?, ?)
            """,
            identifier,
        )


def test_external_identifier_allows_different_identifiers_for_same_release(
    db_connection,
):
    db_connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name
        )
        VALUES (?, ?, ?)
        """,
        (
            "test-game",
            "Test Game",
            "test game",
        ),
    )

    db_connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "test-release",
            "test-game",
            "ps5",
            "Test Game",
        ),
    )

    db_connection.executemany(
        """
        INSERT INTO external_identifier (
            game_release_id,
            service,
            identifier_type,
            value
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                "test-release",
                "playstation_network",
                "title_id",
                "TEST12345",
            ),
            (
                "test-release",
                "playstation_network",
                "trophy_set",
                "NPWR12345",
            ),
        ],
    )

    count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM external_identifier
        """
    ).fetchone()[0]

    assert count == 2


def test_deleting_game_cascades_to_release_and_external_identifiers(
    db_connection,
):
    db_connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name
        )
        VALUES (?, ?, ?)
        """,
        (
            "test-game",
            "Test Game",
            "test game",
        ),
    )

    db_connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "test-release",
            "test-game",
            "ps5",
            "Test Game",
        ),
    )

    db_connection.execute(
        """
        INSERT INTO external_identifier (
            game_release_id,
            service,
            identifier_type,
            value
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "test-release",
            "playstation_network",
            "title_id",
            "TEST12345",
        ),
    )

    db_connection.execute(
        """
        DELETE FROM game
        WHERE id = ?
        """,
        ("test-game",),
    )

    release_count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM game_release
        """
    ).fetchone()[0]

    identifier_count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM external_identifier
        """
    ).fetchone()[0]

    assert release_count == 0
    assert identifier_count == 0


def test_deleting_release_cascades_to_external_identifiers(
    db_connection,
):
    db_connection.execute(
        """
        INSERT INTO game (
            id,
            name,
            sort_name
        )
        VALUES (?, ?, ?)
        """,
        (
            "test-game",
            "Test Game",
            "test game",
        ),
    )

    db_connection.execute(
        """
        INSERT INTO game_release (
            id,
            game_id,
            platform_id,
            name
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "test-release",
            "test-game",
            "ps5",
            "Test Game",
        ),
    )

    db_connection.execute(
        """
        INSERT INTO external_identifier (
            game_release_id,
            service,
            identifier_type,
            value
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "test-release",
            "playstation_network",
            "title_id",
            "TEST12345",
        ),
    )

    db_connection.execute(
        """
        DELETE FROM game_release
        WHERE id = ?
        """,
        ("test-release",),
    )

    identifier_count = db_connection.execute(
        """
        SELECT COUNT(*)
        FROM external_identifier
        """
    ).fetchone()[0]

    assert identifier_count == 0


def test_drop_tables_removes_all_tables(
    empty_db_connection,
):
    create_tables(empty_db_connection)

    drop_tables(empty_db_connection)

    rows = empty_db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    assert rows == []


def test_drop_tables_does_not_fail_when_tables_do_not_exist(
    empty_db_connection,
):
    drop_tables(empty_db_connection)

    rows = empty_db_connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    assert rows == []
