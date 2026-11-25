from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def movies_count(db: AsyncSession) -> int:
    return await db.scalar(select(func.count(MovieModel.id))) or 0


async def all_movies(db: AsyncSession, skip: int, limit: int) -> Sequence[MovieModel]:
    return (
        await db.scalars(
            select(MovieModel).order_by(MovieModel.id.desc()).offset(skip).limit(limit)
        )
    ).all()
