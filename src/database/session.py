import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.settings import get_settings
from database.models import Base

settings = get_settings()

if os.getenv("ENVIRONMENT") == "testing":
    DATABASE_URL = "sqlite+aiosqlite:///test.db"
    engine_args = {"connect_args": {"check_same_thread": False}}
else:
    DATABASE_URL = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
        f"{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}"
    )
    engine_args = {}

engine = create_async_engine(DATABASE_URL, echo=False, **engine_args)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_contextmanager():
    async with AsyncSessionLocal() as session:
        yield session


async def reset_database():
    async with engine.begin() as conn:
        import database.models
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
