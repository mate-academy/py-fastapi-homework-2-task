from typing import Sequence, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreate, MovieUpdate


T = TypeVar("T")


async def get_or_create_entity(db: AsyncSession, model: Type[T], lookup_field: str, **kwargs) -> T:
    lookup_value = kwargs.get(lookup_field)

    if lookup_value is None:
        raise ValueError(f"Missing lookup field '{lookup_field}' in arguments.")

    instance_query = await db.execute(
        select(model).where(getattr(model, lookup_field) == lookup_value)
    )
    instance = instance_query.scalar_one_or_none()

    if not instance:
        instance = model(**kwargs)
        db.add(instance)
        await db.flush()

    return instance


async def read_movies(db: AsyncSession):
    result = await db.execute(select(MovieModel))
    movies = result.scalars().all()

    return movies


async def read_movies_paginated(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10
) -> tuple[Sequence[MovieModel], int | None]:
    offset = (page - 1) * per_page

    count_query = await db.execute(select(func.count(MovieModel.id)))
    total_movies = count_query.scalar()

    movies_query = await db.execute(
        select(MovieModel)
        .limit(per_page)
        .offset(offset)
        .order_by(MovieModel.id.desc())
    )
    movies = movies_query.scalars().all()

    return movies, total_movies


async def create_movie(db: AsyncSession, movie: MovieCreate):
    duplicate_stmt = select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    )
    duplicate_query = await db.execute(duplicate_stmt)

    if duplicate_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie.name}' and release date '{movie.date}' already "
                f"exists."
            )
        )

    country = await get_or_create_entity(db, CountryModel, "code", code=movie.country)
    genres = [
        await get_or_create_entity(db, GenreModel, "name", name=name)
        for name in movie.genres
    ]
    actors = [
        await get_or_create_entity(db, ActorModel, "name", name=name)
        for name in movie.actors
    ]
    languages = [
        await get_or_create_entity(db, LanguageModel, "name", name=name)
        for name in movie.languages
    ]

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie, attribute_names=["country", "genres", "actors", "languages"])

    return new_movie


async def read_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    return movie


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    db_movie = await read_movie(db, movie_id)

    if not db_movie:
        return None

    for key, value in movie.model_dump(exclude_unset=True).items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie, attribute_names=["country", "genres", "actors", "languages"])

    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    db_movie = await read_movie(db, movie_id)

    if not db_movie:
        return None

    await db.delete(db_movie)
    await db.commit()

    return db_movie
