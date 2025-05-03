from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from sqlalchemy.orm import joinedload

from database import MovieModel
from schemas import MovieDetailSchema
from schemas.movies import (
    CountryResponse,
    GenreResponse,
    ActorResponse,
    LanguageResponse,
)


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


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    return movie
