from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas import MovieCreateRequestSchema


async def get_movie_model(movie_id: int, db: AsyncSession) -> Optional[MovieModel]:
    result = await db.execute(
        select(MovieModel).filter(MovieModel.id == movie_id).options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
    )
    return result.scalars().first()


async def get_movies(offset, limit, db: AsyncSession) -> Sequence[MovieModel]:
    query = select(MovieModel).order_by(*MovieModel.default_order_by()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_movie_model_by_name_and_date(name: str, date: date, db: AsyncSession) -> Optional[MovieModel]:
    result = await db.execute(
        select(MovieModel).filter(MovieModel.name == name, MovieModel.date == date)
    )
    return result.scalars().first()


async def get_or_create_country(code: str, db: AsyncSession) -> CountryModel:
    result = await db.execute(
        select(CountryModel).filter(CountryModel.code == code)
    )
    country = result.scalars().first()
    if not country:
        country = CountryModel(code=code)
        db.add(country)
    return country


async def get_or_create_genre(name: str, db: AsyncSession) -> GenreModel:
    result = await db.execute(
        select(GenreModel).filter(GenreModel.name == name)
    )
    genre = result.scalars().first()
    if not genre:
        genre = GenreModel(name=name)
        db.add(genre)
    return genre


async def get_or_create_actor(name: str, db: AsyncSession) -> ActorModel:
    result = await db.execute(
        select(ActorModel).filter(ActorModel.name == name)
    )
    actor = result.scalars().first()
    if not actor:
        actor = ActorModel(name=name)
        db.add(actor)
    return actor


async def get_or_create_language(name: str, db: AsyncSession) -> LanguageModel:
    result = await db.execute(
        select(LanguageModel).filter(LanguageModel.name == name)
    )
    language = result.scalars().first()
    if not language:
        language = LanguageModel(name=name)
        db.add(language)
    return language


async def create_movie_model(movie_data: MovieCreateRequestSchema, db: AsyncSession) -> MovieModel:
    country = await get_or_create_country(movie_data.country, db)
    genres = [await get_or_create_genre(name, db) for name in movie_data.genres]
    actors = [await get_or_create_actor(name, db) for name in movie_data.actors]
    languages = [await get_or_create_language(name, db) for name in movie_data.languages]

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    return new_movie
