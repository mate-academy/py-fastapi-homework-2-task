import datetime
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from crud.actors import find_actors_by_name_or_create
from crud.countries import find_country_by_code_or_create
from crud.genres import find_genre_by_name_or_create
from crud.languages import find_language_by_name_or_create
from database import MovieModel
from schemas.actors import ActorCreate
from schemas.countries import CountryCreate
from schemas.genres import GenreCreate
from schemas.languages import LanguageCreate
from schemas.movies import MovieCreate


async def movies_count(db: AsyncSession) -> int:
    return await db.scalar(select(func.count(MovieModel.id))) or 0


async def all_movies(db: AsyncSession, skip: int, limit: int) -> Sequence[MovieModel]:
    return (
        await db.scalars(
            select(MovieModel).order_by(MovieModel.id.desc()).offset(skip).limit(limit)
        )
    ).all()


async def create_movie_by_data(db: AsyncSession, movie_data: MovieCreate) -> MovieModel:
    country = await find_country_by_code_or_create(
        db=db, country_data=CountryCreate(code=movie_data.country)
    )

    genres = [
        await find_genre_by_name_or_create(
            db=db, genre_data=GenreCreate(name=genre_name)
        )
        for genre_name in dict.fromkeys(movie_data.genres)
    ]

    actors = [
        await find_actors_by_name_or_create(
            db=db, actor_data=ActorCreate(name=actor_name)
        )
        for actor_name in dict.fromkeys(movie_data.actors)
    ]

    languages = [
        await find_language_by_name_or_create(
            db=db, language_data=LanguageCreate(name=language_name)
        )
        for language_name in dict.fromkeys(movie_data.languages)
    ]

    movie = MovieModel(
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

    db.add(movie)
    await db.commit()
    await db.refresh(
        movie, attribute_names=["country", "genres", "actors", "languages"]
    )

    return movie


async def find_movie_by_name_and_date(
    db: AsyncSession, name: str, date: datetime.date
) -> MovieModel | None:
    return await db.scalar(
        select(MovieModel).where(MovieModel.name == name, MovieModel.date == date)
    )
