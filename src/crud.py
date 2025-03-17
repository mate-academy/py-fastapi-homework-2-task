from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel, Base
from database.models import GenreModel, ActorModel, LanguageModel, CountryModel
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def get_movies(db: AsyncSession):
    result = await db.execute(select(MovieModel).order_by(MovieModel.id.desc()))
    films = result.scalars().all()
    return films


async def get_or_create_related_model(db: AsyncSession, model: type[Base], **params):
    instance = model(**params)
    try:
        db.add(instance)
    except IntegrityError:
        filter_params = (getattr(model, key) == params[key] for key in params)
        result = await db.execute(select(model).where(*filter_params))
        instance = result.scalar_one_or_none()
        return instance, False
    else:
        return instance, True


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    attrs = movie.model_dump()
    country_data = attrs.pop("country")
    country, _ = await get_or_create_related_model(db, CountryModel, code=country_data)
    genres, actors, languages = attrs.pop("genres"), attrs.pop("actors"), attrs.pop("languages")

    new_movie = MovieModel(**attrs)
    new_movie.country = country

    for genre in genres:
        instance, _ = await get_or_create_related_model(db, GenreModel, name=genre)
        new_movie.genres.append(instance)
    for actor in actors:
        instance, _ = await get_or_create_related_model(db, ActorModel, name=actor)
        new_movie.actors.append(instance)
    for language in languages:
        instance, _ = await get_or_create_related_model(db, LanguageModel, name=language)
        new_movie.languages.append(instance)

    db.add(new_movie)
    await db.commit()
    return await get_movie(db, new_movie.id)


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(joinedload(MovieModel.country))
        .options(joinedload(MovieModel.genres))
        .options(joinedload(MovieModel.actors))
        .options(joinedload(MovieModel.languages))
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()
    return movie


async def check_movie_exists(db: AsyncSession, name: str, date: datetime.date):
    result = await db.execute(select(MovieModel).where(
        MovieModel.name == name, MovieModel.date == date
    ))
    return bool(result.scalar())


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie


async def update_movie(db: AsyncSession, movie_id: int, update_data: dict):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    updated_model = MovieUpdateSchema(**db_movie.__dict__)
    updated_movie = updated_model.model_copy(update=update_data).model_dump()
    for attr in updated_movie:
        setattr(db_movie, attr, updated_movie[attr])
    await db.commit()
    await db.refresh(db_movie)
    return db_movie
