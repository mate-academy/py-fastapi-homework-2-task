import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from config import get_settings
from database.session_sqlite import (
    reset_sqlite_database,
    get_sqlite_db_contextmanager,
    get_sqlite_db,
)
from database.populate import CSVDatabaseSeeder
from main import app
from routes.movies import get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_db():
    """Reset the SQLite database before each test."""
    await reset_sqlite_database()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_get_db():
    """
    Force FastAPI to use the same database session as the tests.
    """
    app.dependency_overrides[get_db] = get_sqlite_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provide an asynchronous test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide an async database session for seeding and manual checks."""
    async with get_sqlite_db_contextmanager() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def seed_database(db_session):
    """Seed the database with test data."""
    settings = get_settings()
    seeder = CSVDatabaseSeeder(
        csv_file_path=settings.PATH_TO_MOVIES_CSV, db_session=db_session
    )
    await seeder.seed()
    yield db_session
