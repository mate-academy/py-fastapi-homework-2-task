from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import schemas
from database import models
from schemas.movies import MovieListSchema


# Write your code here
async def get_all_movies(
        db: AsyncSession,
        limit: int,
        offset: int
) -> list[models.MovieModel]:
    stmt = select(
        models.MovieModel
    ).order_by(models.MovieModel.id.desc()).offset(offset).limit(limit)
    result = await db.scalars(stmt)
    return result.all()


async def get_movie_by_id(db: AsyncSession, movie_id) -> models.MovieModel | None:
    stmt = select(
        models.MovieModel).where(models.MovieModel.id == movie_id
                                 ).options(
        joinedload(models.MovieModel.country),
        joinedload(models.MovieModel.genres),
        joinedload(models.MovieModel.actors),
        joinedload(models.MovieModel.languages)
    )
    return await db.scalar(stmt)


async def get_amount_movies(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(models.MovieModel)
    result = await db.scalar(stmt)
    return result or 0


async def create_movie(
        db: AsyncSession,
        movie: schemas.MovieCreateSchema
) -> models.MovieModel:
    base_data = movie.model_dump(exclude={"country", "genres", "actors", "languages"})
    db_movie = models.MovieModel(**base_data)

    country_obj = await get_or_create_country(db, movie.country)
    genres_obj = await get_or_create_genres(db, movie.genres)
    actors_obj = await get_or_create_actors(db, movie.actors)
    languages_obj = await get_or_create_languages(db, movie.languages)

    db_movie.country = country_obj
    db_movie.genres = genres_obj
    db_movie.actors = actors_obj
    db_movie.languages = languages_obj

    db.add(db_movie)
    await db.commit()
    await db.refresh(db_movie)

    return db_movie


async def get_or_create_genres(
        db: AsyncSession,
        genres_names: list[str]
) -> list[models.GenreModel]:
    stmt = select(models.GenreModel).where(models.GenreModel.name.in_(genres_names))
    result = await db.scalars(stmt)
    existing_genres = list(result.all())

    existing_names = {genre.name for genre in existing_genres}

    missing_names = set(genres_names) - existing_names

    new_genres = [models.GenreModel(name=name) for name in missing_names]

    if new_genres:
        db.add_all(new_genres)

    return existing_genres + new_genres


async def get_or_create_actors(
        db: AsyncSession,
        actors_names: list[str]
) -> list[models.ActorModel]:
    stmt = select(models.ActorModel).where(models.ActorModel.name.in_(actors_names))
    result = await db.scalars(stmt)
    existing_actors = list(result.all())

    existing_names = {actor.name for actor in existing_actors}

    missing_names = set(actors_names) - existing_names

    new_actors = [models.ActorModel(name=name) for name in missing_names]

    if new_actors:
        db.add_all(new_actors)

    return existing_actors + new_actors


async def get_or_create_languages(
        db: AsyncSession,
        languages_names: list[str]
) -> list[models.LanguageModel]:

    stmt = select(
        models.LanguageModel
    ).where(models.LanguageModel.name.in_(languages_names))

    result = await db.scalars(stmt)

    existing_languages = list(result.all())

    existing_names = {language.name for language in existing_languages}

    missing_languages = set(languages_names) - existing_names

    new_languages = [
        models.LanguageModel(name=name) for name in missing_languages
    ]

    if new_languages:
        db.add_all(new_languages)

    return new_languages + existing_languages


async def get_or_create_country(
        db: AsyncSession,
        country_code: str
) -> models.CountryModel:
    stmt = select(
        models.CountryModel
    ).where(models.CountryModel.code == country_code)
    db_country = await db.scalar(stmt)

    if db_country:
        return db_country

    new_country = models.CountryModel(code=country_code)
    db.add(new_country)

    return new_country


async def update_film(
        db: AsyncSession,
        movie_id: int,
        movie_data: schemas.MovieUpdateSchema
) -> models.MovieModel | None:
    result = await db.execute(
        select(models.MovieModel).where(models.MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        return None

    update_data = movie_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(models.MovieModel).where(models.MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        return None

    await db.delete(db_movie)
    await db.commit()
    return True
