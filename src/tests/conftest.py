import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from src.database.models import Base
from src.config import get_settings
from src.database import get_db_contextmanager
from src.database.populate import CSVDatabaseSeeder
from src.main import app


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous test client for making HTTP requests."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session for database interactions.
    """
    async with get_db_contextmanager() as session:
        yield session


# --- FIXED FIXTURES START HERE ---


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_clean_setup(db_session: AsyncSession):
    """
    Guaranteed clean up: Drops and recreates the schema before *every* test.
    Crucially, it *does not* load any data, ensuring tests like
    'test_get_movies_empty_database' run against an empty database.
    """
    engine = db_session.bind

    if engine is None:
        raise ValueError("Database engine is not bound to the session.")

    # Drop all tables and recreate them to ensure a clean slate
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # We yield the session after cleanup.
    yield db_session


@pytest_asyncio.fixture(scope="function")
async def seed_database(db_session: AsyncSession, db_clean_setup):
    """
    Explicitly seeds the database for tests that require data.
    This fixture must be explicitly listed as a dependency in the tests
    that need the data loaded (e.g., test_get_movies_default_parameters).
    """
    settings = get_settings()
    # The session is clean because of db_clean_setup
    seeder = CSVDatabaseSeeder(
        csv_file_path=settings.PATH_TO_MOVIES_CSV, db_session=db_session
    )
    await seeder.seed()

    # Commit after seeding to ensure data is available for the test
    await db_session.commit()

    # We yield the session containing the seeded data
    yield db_session


# For compatibility with potential old test file dependency names:
@pytest_asyncio.fixture(scope="function", autouse=False)
async def forced_db_reset_and_seed(seed_database) -> AsyncGenerator:
    """
    Compatibility fixture: acts as the old 'forced_db_reset_and_seed'
    but only runs if explicitly requested by a test dependency.
    """
    yield seed_database
