import asyncio
from typing import Type

from pydantic import ValidationError
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException
from sqlalchemy.orm import joinedload

from database import MovieModel, Base
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieDetailSchema
from schemas.movies import (
    CountryResponse,
    GenreResponse,
    ActorResponse,
    LanguageResponse,
    MovieCreateSchema,
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


async def create_new_movie(movie: MovieCreateSchema, db: AsyncSession):
    movie_db = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    if movie_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in movie.genres:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == name)
        )
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
            genres.append(genre)

    actors = []
    for name in movie.actors:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == name)
        )
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
            actors.append(actor)

    languages = []
    for name in movie.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
            languages.append(language)

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
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(
        new_movie, attribute_names=["country", "genres", "actors", "languages"]
    )
    return new_movie


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
