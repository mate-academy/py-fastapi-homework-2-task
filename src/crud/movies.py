from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from crud.another import (
    get_or_create_country,
    get_or_create_actors,
    get_or_create_genres,
    get_or_create_languages
)
from database import MovieModel
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def read_movie(movie_id: int, db: AsyncSession):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .execution_options(populate_existing=True)
    )

    movie = result.unique().scalar_one_or_none()
    return movie


async def post_movie(movie: MovieCreateSchema, db: AsyncSession):
    result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    existing_movie = result.scalars().first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = await get_or_create_country(db, movie.country)
    genres = await get_or_create_genres(db, movie.genres)
    actors = await get_or_create_actors(db, movie.actors)
    languages = await get_or_create_languages(db, movie.languages)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        actors=actors,
        languages=languages,
        genres=genres,
    )
    db.add(new_movie)
    await db.commit()

    return new_movie


async def delete_movie(movie_id: int, db: AsyncSession):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        return None
    await db.delete(movie)
    await db.commit()
    return True


async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    update_data = movie.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()
    await db.refresh(db_movie)
    return db_movie
