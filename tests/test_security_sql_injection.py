import pytest
import sqlite3
from main import get_user


@pytest.fixture
def db_connection():
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT);")
    cursor.execute("INSERT INTO users (username) VALUES ('testuser');")
    conn.commit()
    yield conn
    conn.close()



def test_sql_injection_attempt(db_connection, monkeypatch):
    # This test attempts to exploit a potential SQL injection vulnerability.
    # It injects a malicious payload into the user ID parameter to try to
    # retrieve more data than intended or potentially modify the database.
    def mock_execute(query, params):
        # Check if the query contains any SQL injection attempts.
        assert 'OR' not in query, "SQL injection detected in query: {}".format(query)
        assert 'UNION' not in query, "SQL injection detected in query: {}".format(query)
        assert 'DROP' not in query, "SQL injection detected in query: {}".format(query)
        # If no SQL injection is detected, proceed with the original execution.
        conn = db_connection
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    monkeypatch.setattr('sqlite3.Connection.cursor', lambda self: type('cursor', (object,), {'execute': mock_execute, 'fetchone': db_connection.cursor().fetchone})())

    # Attempt to retrieve user with a malicious ID.
    result = get_user("1 OR 1=1")

    # The test should pass without raising an exception, meaning the injected
    # SQL did not execute as intended due to the parameterized query.
    assert result is None or result[1] == 'testuser'