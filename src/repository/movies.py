from typing import Sequence, TypeVar

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel, Base

T = TypeVar("T", bound=Base)


async def get_movies(per_page: int, page: int, db: AsyncSession) -> Sequence[MovieModel]:
    movies = await db.execute(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    return movies.scalars().all()


async def get_number_of_movies(db: AsyncSession) -> int:
    return (await db.execute(select(func.count()).select_from(MovieModel))).scalar()


async def get_movie(db: AsyncSession, **kwargs) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .filter_by(**kwargs)
    )
    return result.unique().scalar_one_or_none()


async def get_or_create(db_model: type[T], db: AsyncSession, **kwargs) -> T:
    result = await db.execute(select(db_model).filter_by(**kwargs))

    if db_record := result.unique().scalar_one_or_none():
        return db_record

    new_record = db_model(**kwargs)
    db.add(new_record)
    await db.flush()

    return new_record


async def get_movie_or_404(movie_id: int, db: AsyncSession) -> MovieModel:

    if movie := await get_movie(db, id=movie_id):
        return movie

    raise HTTPException(
        status_code=404,
        detail="Movie with the given ID was not found."
    )
