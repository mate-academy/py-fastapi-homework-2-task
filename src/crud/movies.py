from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from database import MovieModel


def build_page_url(page_num: int, per_page: int) -> str:
    # such path should be according to the task, not absolute url
    return f"/theater/movies/?page={page_num}&per_page={per_page}"


async def get_paginated_movies(db: AsyncSession, offset: int, limit: int):
    result = await db.execute(
        select(MovieModel)
        .offset(offset)
        .limit(limit)
        .order_by(desc(MovieModel.id))
    )
    movies = result.scalars().all()
    return movies


async def get_movies_count(db: AsyncSession):
    total_count = await db.execute(
        select(func.count()).select_from(MovieModel)
    )
    return total_count.scalar_one()
