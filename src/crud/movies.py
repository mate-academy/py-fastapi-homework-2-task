from fastapi import HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from starlette import status

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieUpdate


async def get_movies_paginated(db: AsyncSession, page: int, per_page: int):
    total_query = select(func.count()).select_from(MovieModel)
    total_result = await db.execute(total_query)
    total_items = total_result.scalar()

    offset = (page - 1) * per_page
    movie_query = select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)

    result = await db.execute(movie_query)

    movies = result.unique().scalars().all()

    return movies, total_items


async def _get_or_create_related(db: AsyncSession, model, field_name: str, value: str, **extra_attrs):
    query = select(model).where(getattr(model, field_name) == value)
    result = await db.execute(query)
    obj = result.scalar_one_or_none()

    if not obj:
        obj = model(**{field_name: value}, **extra_attrs)
        db.add(obj)
    return obj


async def create_movie(db: AsyncSession, movie_in: MovieCreateSchema):
    existing_movie = await db.execute(
        select(MovieModel).where(MovieModel.name == movie_in.name, MovieModel.date == movie_in.date)
    )
    if existing_movie.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    movie_data = movie_in.model_dump(exclude={"country", "genres", "actors", "languages"})

    country_obj = await _get_or_create_related(
        db,
        CountryModel,
        "name",
        movie_in.country,
        code=movie_in.country[:2].upper()
    )

    genre_objs = [await _get_or_create_related(db, GenreModel, "name", g) for g in movie_in.genres]
    actor_objs = [await _get_or_create_related(db, ActorModel, "name", a) for a in movie_in.actors]
    lang_objs = [await _get_or_create_related(db, LanguageModel, "name", i) for i in movie_in.languages]

    new_movie = MovieModel(
        **movie_data,
        country=country_obj,
        genres=genre_objs,
        actors=actor_objs,
        languages=lang_objs
    )

    db.add(new_movie)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"DEBUG ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(query)
    return result.unique().scalar_one()


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def delete_movie(db: AsyncSession, movie_id: int):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if movie:
        await db.delete(movie)
        await db.commit()
        return movie
    return None


async def update_movie(db: AsyncSession, movie_id: int, movie_in: MovieUpdate):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        return None

    update_data = movie_in.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)
    await db.commit()
    return movie
