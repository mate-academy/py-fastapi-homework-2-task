import pycountry
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel, ActorModel, LanguageModel, CountryModel
from database import get_db, MovieModel

from datetime import date, timedelta

from schemas import MovieCreate


async def check_for_actor_in_database(
        actor: str,
        db: AsyncSession = Depends(get_db)
):
    db_actor = await db.scalar(
        select(ActorModel)
        .where(ActorModel.name == actor)
    )

    return db_actor


async def check_for_genre_in_database(
        genre: str,
        db: AsyncSession = Depends(get_db)
):
    db_genre = await db.scalar(
        select(GenreModel)
        .where(GenreModel.name == genre)
    )

    return db_genre


async def check_for_language_in_database(
        language: str,
        db: AsyncSession = Depends(get_db)
):
    db_language = await db.scalar(
        select(LanguageModel)
        .where(LanguageModel.name == language)
    )

    return db_language


async def check_for_country_in_database(
        code: str,
        db: AsyncSession = Depends(get_db)
):
    db_country = await db.scalar(
        select(CountryModel)
        .where(CountryModel.code == code)
    )

    return db_country


async def check_for_movie_in_database(
        movie: MovieCreate,
        db: AsyncSession = Depends(get_db)
):
    db_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )

    return db_movie


async def create_genre(genre: str, db: AsyncSession = Depends(get_db)):
    db_genre = GenreModel(name=genre)
    db.add(db_genre)
    await db.commit()
    await db.refresh(db_genre)

    return db_genre


async def create_actor(name: str, db: AsyncSession = Depends(get_db)):
    actor = ActorModel(name=name)
    db.add(actor)
    await db.commit()
    await db.refresh(actor)

    return actor


async def create_language(name: str, db: AsyncSession = Depends(get_db)):
    language = LanguageModel(name=name)
    db.add(language)
    await db.commit()
    await db.refresh(language)

    return language


async def create_country(code: str, db: AsyncSession = Depends(get_db)):
    country = pycountry.countries.get(alpha_3=code)
    db_country = CountryModel(code=code, name=country.name if country else None)
    db.add(db_country)
    await db.commit()
    await db.refresh(db_country)
    return db_country


async def check_for_date(movie_date: date):
    if movie_date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")


async def check_for_name_len(name: str):
    if len(name) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")
