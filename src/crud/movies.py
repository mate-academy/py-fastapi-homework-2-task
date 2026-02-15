from datetime import date
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def get_movies_paginated(
    db: AsyncSession,
    *,
    page: int,
    per_page: int,
) -> tuple[Sequence[MovieModel], int]:

    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.scalars(stmt)
    movies = result.all()

    return movies, total_items or 0


async def get_movie_by_id(
    db: AsyncSession,
    movie_id: int,
) -> MovieModel | None:

    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    movie = await db.scalar(stmt)
    return movie


async def get_movie_by_name_and_date(
    db: AsyncSession,
    name: str,
    release_date: date,
) -> MovieModel | None:

    stmt = select(MovieModel).where(
        MovieModel.name == name,
        MovieModel.date == release_date,
    )

    return await db.scalar(stmt)


async def _get_or_create_country(
    db: AsyncSession,
    code: str,
) -> CountryModel:

    stmt = select(CountryModel).where(CountryModel.code == code)
    country = await db.scalar(stmt)

    if country:
        return country

    country = CountryModel(code=code)
    db.add(country)
    await db.flush()

    return country


async def _get_or_create_by_name(
    db: AsyncSession,
    model,
    name: str,
):
    stmt = select(model).where(model.name == name)
    obj = await db.scalar(stmt)

    if obj:
        return obj

    obj = model(name=name)
    db.add(obj)
    await db.flush()

    return obj


async def create_movie(
    db: AsyncSession,
    data: MovieCreateSchema,
) -> MovieModel:

    country = await _get_or_create_country(db, data.country)

    genres = [
        await _get_or_create_by_name(db, GenreModel, name)
        for name in data.genres
    ]

    actors = [
        await _get_or_create_by_name(db, ActorModel, name)
        for name in data.actors
    ]

    languages = [
        await _get_or_create_by_name(db, LanguageModel, name)
        for name in data.languages
    ]

    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    movie = await db.scalar(stmt)

    return movie


async def update_movie(
    db: AsyncSession,
    movie: MovieModel,
    data: MovieUpdateSchema,
) -> None:

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()
    await db.refresh(movie)


async def delete_movie(
    db: AsyncSession,
    movie: MovieModel,
) -> None:

    await db.delete(movie)
    await db.commit()
