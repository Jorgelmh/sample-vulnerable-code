import pytest
import aiosqlite
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
async def test_db():
    db = await aiosqlite.connect('test.db')
    cursor = await db.cursor()
    await cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT
        )
    ''')
    await cursor.execute("INSERT OR IGNORE INTO users (username, email) VALUES ('alice', 'alice@example.com')")
    await cursor.execute("INSERT OR IGNORE INTO users (username, email) VALUES ('bob', 'bob@example.com')")
    await db.commit()
    yield db
    await cursor.execute("DROP TABLE IF EXISTS users")
    await db.commit()
    await db.close()


@pytest.fixture
def test_client():
    return TestClient(app)


async def insert_user(db, username, email):
    cursor = await db.cursor()
    await cursor.execute("INSERT INTO users (username, email) VALUES (?, ?)", (username, email))
    await db.commit()


@pytest.mark.asyncio
async def test_get_user_valid(test_db, test_client):
    # Test case 1: Verify retrieving a valid user.
    response = test_client.get("/users/alice")
    assert response.status_code == 200
    assert response.json() == {"username": "alice", "email": "alice@example.com"}


@pytest.mark.asyncio
async def test_get_user_invalid(test_db, test_client):
    # Test case 2: Verify retrieving an invalid user.
    response = test_client.get("/users/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"error": "User not found"}


@pytest.mark.asyncio
async def test_sql_injection_attempt_1(test_db, test_client):
    # Test case 3: Attempt SQL injection with a simple payload.
    # The fix should prevent this from returning unintended data.
    response = test_client.get("/users/' OR '1'='1")
    assert response.status_code == 200
    assert response.json() == {"error": "User not found"}


@pytest.mark.asyncio
async def test_sql_injection_attempt_2(test_db, test_client):
    # Test case 4: Attempt SQL injection with a different payload.
    # The fix should prevent this from returning unintended data.
    response = test_client.get("/users/admin'--")
    assert response.status_code == 200
    # Expecting user not found or the literal string. The important part is that injection doesn't work
    assert response.json() == {"error": "User not found"}


@pytest.mark.asyncio
async def test_sql_injection_attempt_3(test_db, test_client):
    # Test case 5: Attempt SQL injection that might return all users.
    response = test_client.get("/users/' OR username LIKE '%' --")
    assert response.status_code == 200
    assert response.json() == {"error": "User not found"}


@pytest.mark.asyncio
async def test_sql_injection_attempt_4(test_db, test_client):
    # Test case 6: Attempt SQL injection to cause an error and potentially reveal database information.
    response = test_client.get("/users/'; DROP TABLE users; --")
    assert response.status_code == 200
    assert response.json() == {"error": "User not found"}


@pytest.mark.asyncio
async def test_sql_injection_attempt_5(test_db, test_client):
    # Test case 7: Attempt SQL injection to select a specific user using a crafted payload.
    response = test_client.get("/users/alice' AND email LIKE 'alice@example.com' --")
    assert response.status_code == 200
    assert response.json() == {"error": "User not found"}