from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    CountryCreateSchema,
    GenreCreateSchema,
    ActorCreateSchema,
    LanguageCreateSchema
)


async def get_movies(db: AsyncSession, page: int = 1, per_page: int = 10):
    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)
    total_items = count_result.scalar()

    if total_items == 0:
        return None

    offset = (page - 1) * per_page

    query = select(MovieModel).limit(per_page).offset(offset)
    result = await db.execute(query)
    movies = result.scalars().all()

    return movies, total_items


async def get_movie_by_name_date(
    db: AsyncSession,
    movie_name: str,
    movie_date: date
):
    query = select(MovieModel).where(
        and_(
            MovieModel.name == movie_name,
            MovieModel.date == movie_date
        )
    )
    result = await db.execute(query)
    movie = result.scalar_one_or_none()
    return movie


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    query = select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()
    return movie


async def get_country_by_code(db: AsyncSession, county_code: str):
    query = select(CountryModel).where(CountryModel.code == county_code)
    result = await db.execute(query)
    country = result.scalar_one_or_none()
    return country


async def create_country(db: AsyncSession, country: CountryCreateSchema):
    new_country = CountryModel(**country.model_dump())
    db.add(new_country)
    await db.commit()
    await db.refresh(new_country)
    return new_country


async def get_genre_by_name(db: AsyncSession, genre_name: str):
    query = select(GenreModel).where(GenreModel.name == genre_name)
    result = await db.execute(query)
    genre = result.scalar_one_or_none()
    return genre


async def create_genre(db: AsyncSession, genre: GenreCreateSchema):
    new_genre = GenreModel(**genre.model_dump())
    db.add(new_genre)
    await db.commit()
    await db.refresh(new_genre)
    return new_genre


async def get_actor_by_name(db: AsyncSession, actor_name: str):
    query = select(ActorModel).where(ActorModel.name == actor_name)
    result = await db.execute(query)
    actor = result.scalar_one_or_none()
    return actor


async def create_actor(db: AsyncSession, actor: ActorCreateSchema):
    new_actor = ActorModel(**actor.model_dump())
    db.add(new_actor)
    await db.commit()
    await db.refresh(new_actor)
    return new_actor


async def get_language_by_name(db: AsyncSession, language_name: str):
    query = select(LanguageModel).where(LanguageModel.name == language_name)
    result = await db.execute(query)
    language = result.scalar_one_or_none()
    return language


async def create_language(db: AsyncSession, language: LanguageCreateSchema):
    new_language = LanguageModel(**language.model_dump())
    db.add(new_language)
    await db.commit()
    await db.refresh(new_language)
    return new_language
