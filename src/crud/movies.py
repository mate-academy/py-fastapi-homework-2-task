import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MoviePatchSchema


async def get_paginated_movies_list(
        db_session: AsyncSession,
        page: int,
        per_page: int,
) -> tuple:
    offset = (page - 1) * per_page
    movies = await db_session.scalars(select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page))
    count = await db_session.scalar(select(func.count()).select_from(MovieModel))
    return list(movies.all()), count


async def get_movie_by_id(
        db_session: AsyncSession,
        movie_id: int,
) -> MovieModel | None:
    statement = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return await db_session.scalar(statement)


async def get_movie_by_name_and_date(
        db_session: AsyncSession,
        movie_name: str,
        movie_date: datetime.date,
) -> MovieModel | None:
    return await db_session.scalar(
        select(MovieModel)
        .where(MovieModel.name == movie_name)
        .where(MovieModel.date == movie_date)
    )


async def get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    country = await db.scalar(select(CountryModel).where(CountryModel.code == code))
    if country is None:
        country = CountryModel(code=code)
        db.add(country)
        await db.flush()
    return country


async def get_or_create_by_name(db_session: AsyncSession, model, name: str):
    """Works for GenreModel, ActorModel and LanguageModel (all have `name`)."""
    obj = await db_session.scalar(select(model).where(model.name == name))
    if obj is None:
        obj = model(name=name)
        db_session.add(obj)
        await db_session.flush()
    return obj


async def create_movie(
        db_session: AsyncSession,
        movie_data: MovieCreateSchema,
):
    country = await get_or_create_country(db_session, movie_data.country)
    genres = [
        await get_or_create_by_name(db_session, GenreModel, name)
        for name in movie_data.genres
    ]
    actors = [
        await get_or_create_by_name(db_session, ActorModel, name)
        for name in movie_data.actors
    ]
    languages = [
        await get_or_create_by_name(db_session, LanguageModel, name)
        for name in movie_data.languages
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
    db_session.add(movie)
    await db_session.commit()
    return await get_movie_by_id(db_session, movie.id)


async def patch_movie(
        db_session: AsyncSession,
        movie_id: int,
        movie_data: MoviePatchSchema,
):
    values = movie_data.model_dump(exclude_unset=True)
    if not values:
        return
    statement = update(MovieModel).where(MovieModel.id == movie_id).values(**values)
    await db_session.execute(statement)
    await db_session.commit()
