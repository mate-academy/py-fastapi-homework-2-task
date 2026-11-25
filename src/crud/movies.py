from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def movies_count(db: AsyncSession):
    return await db.scalar(select(func.count(MovieModel.id)))


async def all_movies(db: AsyncSession, skip: int, limit: int):
    return await db.scalars(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(skip).limit(limit)
    )
