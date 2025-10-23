from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.settings import get_settings

settings = get_settings()

POSTGRESQL_DATABASE_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
    quote_plus(settings.POSTGRES_USER),
    quote_plus(settings.POSTGRES_PASSWORD),
    settings.POSTGRES_HOST,
    settings.POSTGRES_PORT,
    settings.POSTGRES_DB,
)

postgresql_engine = create_async_engine(POSTGRESQL_DATABASE_URL, echo=False)
AsyncPostgresqlSessionLocal = sessionmaker(  # type: ignore
    bind=postgresql_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

sync_database_url = POSTGRESQL_DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
sync_postgresql_engine = create_engine(sync_database_url, echo=False)


async def get_postgresql_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session.
    """
    async with AsyncPostgresqlSessionLocal() as session:
        yield session


get_db = get_postgresql_db


@asynccontextmanager
async def get_postgresql_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session using a context manager.
    """
    async with AsyncPostgresqlSessionLocal() as session:
        yield session
