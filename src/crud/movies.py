from typing import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import selectinload
from sqlalchemy.sql.expression import desc

import schemas
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from sqlalchemy import select
import datetime
from fastapi import HTTPException


async def get_movies_list(
    db: AsyncSession, skip: int = 0, limit: int = 10
) -> Sequence[MovieModel]:
    result = await db.scalars(
        select(MovieModel).order_by(desc(MovieModel.id)).offset(skip).limit(limit)
    )
    movies = result.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return movies


async def create_country(
    db: AsyncSession, country: schemas.CountryCreateSchema
) -> CountryModel:
    db_country = CountryModel(
        name=country.name,
        code=country.code,
    )
    db.add(db_country)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Country already exists")

    await db.refresh(db_country)
    return db_country


async def create_genre(
    db: AsyncSession, genre: schemas.GenreCreateSchema
) -> GenreModel:
    db_genre = GenreModel(name=genre.name)
    db.add(db_genre)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Genre already exists")

    await db.refresh(db_genre)
    return db_genre


async def create_actor(
    db: AsyncSession, actor: schemas.ActorCreateSchema
) -> ActorModel:
    db_actor = ActorModel(name=actor.name)
    db.add(db_actor)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Actor already exists")

    await db.refresh(db_actor)
    return db_actor


async def create_language(
    db: AsyncSession, language: schemas.LanguageCreateSchema
) -> LanguageModel:
    db_language = LanguageModel(name=language.name)
    db.add(db_language)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Language already exists")

    await db.refresh(db_language)
    return db_language


async def get_or_create_country(country_code, db: AsyncSession) -> CountryModel:
    country_obj = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    if not country_obj:
        country_schema = schemas.CountryCreateSchema(code=country_code, name=None)
        country_obj = await create_country(db=db, country=country_schema)
        return country_obj
    return country_obj


async def get_or_create_genre(genre_name, db: AsyncSession) -> GenreModel:
    genre_obj = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))
    if not genre_obj:
        genre_schema = schemas.GenreCreateSchema(name=genre_name)
        genre_obj = await create_genre(db, genre_schema)
        return genre_obj
    return genre_obj


async def get_or_create_actor(actor_name, db: AsyncSession) -> ActorModel:
    actor_obj = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))
    if not actor_obj:
        actor_schema = schemas.ActorCreateSchema(name=actor_name)
        actor_obj = await create_actor(db, actor_schema)
        return actor_obj
    return actor_obj


async def get_or_create_language(language_name, db: AsyncSession) -> LanguageModel:
    language_obj = await db.scalar(
        select(LanguageModel).where(LanguageModel.name == language_name)
    )
    if not language_obj:
        language_schema = schemas.LanguageCreateSchema(name=language_name)
        language_obj = await create_language(db, language_schema)
        return language_obj
    return language_obj


async def check_duplicate_movie(
    movie_name: str, movie_data: datetime.date, db: AsyncSession
) -> None:
    movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_name, MovieModel.date == movie_data
        )
    )
    if movie is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_name}' and release date '{movie_data}' already exists.",
        )


async def get_movie_by_id(movie_id: int, db: AsyncSession) -> MovieModel:
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

    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


async def create_movie(
    movie: schemas.MovieCreateSchema,
    db: AsyncSession,
) -> MovieModel:
    await check_duplicate_movie(movie_name=movie.name, movie_data=movie.date, db=db)
    country = await get_or_create_country(country_code=movie.country, db=db)

    genres = []
    for genre in movie.genres:
        genres.append(await get_or_create_genre(genre_name=genre, db=db))

    actors = []
    for actor in movie.actors:
        actors.append(await get_or_create_actor(actor_name=actor, db=db))

    languages = []
    for language in movie.languages:
        languages.append(await get_or_create_language(language_name=language, db=db))

    db_movie = MovieModel(
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

    db.add(db_movie)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Movie already exists.")

    await db.refresh(
        db_movie,
        attribute_names=[
            "country",
            "genres",
            "actors",
            "languages",
        ],
    )

    return db_movie


async def delete_movie(movie: MovieModel, db: AsyncSession) -> None:
    await db.delete(movie)
    await db.commit()


async def patch_movie(
    db_movie: MovieModel, db: AsyncSession, movie: schemas.MovieUpdateSchema
) -> MovieModel:
    for field, value in movie.model_dump(exclude_unset=True).items():
        setattr(db_movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    await db.refresh(db_movie)
    return db_movie
