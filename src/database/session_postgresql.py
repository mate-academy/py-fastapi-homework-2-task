from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.settings import get_settings, TestingSettings

settings = get_settings()

# 🔧 Условное переключение между PostgreSQL и SQLite
if isinstance(settings, TestingSettings):
    POSTGRESQL_DATABASE_URL = f"sqlite+aiosqlite:///{settings.PATH_TO_DB}"
else:
    POSTGRESQL_DATABASE_URL = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}"
    )

# 🔧 Асинхронный движок
async_engine = create_async_engine(POSTGRESQL_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# 🔧 Синхронный движок (если нужен)
sync_database_url = POSTGRESQL_DATABASE_URL.replace(
    "postgresql+asyncpg", "postgresql"
).replace("sqlite+aiosqlite", "sqlite")
sync_engine = create_engine(sync_database_url, echo=False)


async def get_postgresql_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_postgresql_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
