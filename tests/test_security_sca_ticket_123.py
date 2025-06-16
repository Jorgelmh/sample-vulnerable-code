import pytest
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient


app = FastAPI()

@app.get("/user/{id}")
def get_user(id):
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,)) # Use parameterized query
    result = cursor.fetchone()
    conn.close()
    return result


@pytest.fixture(scope="module", autouse=True)
def test_db():
    # Setup test database
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)")
    cursor.execute("INSERT INTO users (username) VALUES ('testuser')")
    conn.commit()
    conn.close()
    yield
    # Teardown test database
    import os
    os.remove('test_users.db')




client = TestClient(app)

def test_sql_injection_attempt():
    # Test SQL injection attempt
    # This test tries to inject a SQL command to retrieve all usernames.
    response = client.get("/user/1 UNION SELECT username FROM users")
    assert response.status_code == 200
    # The parameterized query should prevent the injection, so it should not return
    # the username in the response. The response should only contain the data
    # related to the id '1'.
    user = response.json()
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", ("1",))
    expected = cursor.fetchone()
    conn.close()
    assert user == list(expected)


def test_valid_user_id():
    # Test with a valid user ID
    response = client.get("/user/1")
    assert response.status_code == 200
    assert response.json() is not None


def test_invalid_user_id():
    # Test with an invalid user ID
    response = client.get("/user/999")
    assert response.status_code == 200
    assert response.json() is None