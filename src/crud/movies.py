import datetime

from fastapi import Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import schemas
from crud.countries import get_or_create_country
from database import models
from schemas.movies import MovieCreateScheme


async def get_all_movies(
    db: AsyncSession, page: int, per_page: int
) -> list[models.MovieModel]:
    stmt = (
        select(models.MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(models.MovieModel.id.desc())
    )
    movies = await db.scalars(stmt)
    return list(movies)


async def get_movie_by_name_and_date(
    db: AsyncSession, name: str, date: datetime.date
):
    result = await db.execute(
        select(models.MovieModel).where(
            models.MovieModel.name == name, models.MovieModel.date == date
        )
    )
    return result.scalar_one_or_none()


async def get_or_create_by_name(
    db: AsyncSession, model, names: list[str]
) -> list:
    objects = []
    for name in dict.fromkeys(names):  # dedupe, keep order
        obj = await db.scalar(select(model).where(model.name == name))
        if obj is None:
            obj = model(name=name)
            db.add(obj)
            await db.flush()  # so later lookups/ids see it
        objects.append(obj)
    return objects


async def create_movie_db(
    db: AsyncSession, movie_data: MovieCreateScheme
) -> models.MovieModel:
    country = await get_or_create_country(db, str(movie_data.country))
    genres = await get_or_create_by_name(
        db, models.GenreModel, movie_data.genres
    )
    actors = await get_or_create_by_name(
        db, models.ActorModel, movie_data.actors
    )
    languages = await get_or_create_by_name(
        db, models.LanguageModel, movie_data.languages
    )

    movie = models.MovieModel(
        **movie_data.model_dump(
            exclude={"country", "genres", "actors", "languages"}
        ),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.flush()
    movie_id = movie.id
    await db.commit()

    result = await db.execute(
        select(models.MovieModel)
        .where(models.MovieModel.id == movie_id)
        .options(
            selectinload(models.MovieModel.country),
            selectinload(models.MovieModel.genres),
            selectinload(models.MovieModel.actors),
            selectinload(models.MovieModel.languages),
        )
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def patch_movie(
    db: AsyncSession, movie_id: int, movie: schemas.MovieUpdateScheme
) -> bool:
    db_movie = await db.scalar(
        select(models.MovieModel).where(models.MovieModel.id == movie_id)
    )
    if not db_movie:
        return False
    data = movie.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_movie, key, value)
    db.add(db_movie)
    await db.commit()
    await db.refresh(db_movie)
    return True
