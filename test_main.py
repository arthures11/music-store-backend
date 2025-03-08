import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db, async_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

test_engine = create_async_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, future=True
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession, expire_on_commit=False)



async def override_get_db():
    async with TestingSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


app.dependency_overrides[get_db] = override_get_db



@pytest.fixture(scope="session")
def event_loop():
    """creating an instance of the default event loop for each test case."""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


client = TestClient(app)


def test_read_tracks_no_auth():
    response = client.get("/api/tracks/")
    assert response.status_code == 401  # expecting "401 Unauthorized"


def test_read_tracks_with_auth():
    # first getting token with fake user
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = client.get("/api/tracks/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_tracks_with_filter():

    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = client.get("/api/tracks/?name=Love", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_invalid_login():
    response = client.post(
        "/token", data={"username": "artur", "password": "bryja"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect username or password"}