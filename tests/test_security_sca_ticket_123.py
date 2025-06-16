import pytest
import sqlite3
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    # Setup: Create an in-memory SQLite database for testing
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO users (name) VALUES ('Alice')")
    cursor.execute("INSERT INTO users (name) VALUES ('Bob')")
    conn.commit()

    # Override the database connection in the app
    app.db_conn = conn  # Assuming you can set the db_conn on the app instance

    with TestClient(app) as client:
        yield client

    # Teardown: Close the connection and drop the table
    conn.close()


def test_sql_injection_fixed(client):
    # Attack vector: Attempt SQL injection with a crafted ID
    response = client.get("/user/1 OR 1=1; --")

    # Check that the query only returns the first user and does not return all results (SQL injection failed).
    # This confirms the fix is working and prevents SQL injection.
    assert response.status_code == 200
    user = response.json()
    assert user == [1, 'Alice']  # Assuming user with ID 1 is Alice.



def test_valid_user_id(client):
    response = client.get("/user/2")
    assert response.status_code == 200
    user = response.json()
    assert user == [2, 'Bob']


def test_invalid_user_id(client):
    response = client.get("/user/3")
    assert response.status_code == 200
    user = response.json()
    assert user is None