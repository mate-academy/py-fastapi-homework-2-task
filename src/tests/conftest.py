import pytest
from fastapi.testclient import TestClient

from src.config.settings import get_settings
from src.database import (
    reset_database,
    get_db_contextmanager,
)
from src.database.populate import CSVDatabaseSeeder
from src.main import app


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    reset_database()


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    with get_db_contextmanager() as session:
        yield session


@pytest.fixture(scope="function")
def seed_database(db_session):
    settings = get_settings()
    seeder = CSVDatabaseSeeder(csv_file_path=settings.PATH_TO_MOVIES_CSV, db_session=db_session)
    if not seeder.is_db_populated():
        seeder.seed()
    yield db_session
