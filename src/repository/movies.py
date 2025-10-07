from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from database.models import MovieModel
from schemas.movies import MovieUpdateSchema


async def get_movie(db: AsyncSession, movie_id: int):
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
    movie = result.unique().scalar_one_or_none()
    return movie


async def get_movies(page: int, per_page: int, db: AsyncSession):
    result = await db.execute(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    movies = result.scalars().all()
    return movies


async def get_movies_count(db: AsyncSession):
    count = await db.scalar(select(func.count(MovieModel.id)))
    return count


async def update_movie(
    db: AsyncSession, movie: MovieModel, movie_data: MovieUpdateSchema
):
    try:
        for attr, value in movie_data.model_dump(exclude_unset=True).items():
            setattr(movie, attr, value)

        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return movie


async def delete_film(db: AsyncSession, movie_id: int) -> None:
    movie = await get_movie(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None
