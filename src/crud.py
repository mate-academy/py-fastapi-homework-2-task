from typing import Callable, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.sql.functions import count

from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    CountryModel,
)
from schemas.movies import MovieCreate


def with_relations(*relations: str):
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            if result:
                await kwargs["db"].refresh(result, relations)

            return result

        return wrapper

    return decorator


async def get_or_create(db, model, value, field_name="name"):
    result = await db.execute(select(model).where(getattr(model, field_name) == value))
    entity = result.scalar_one_or_none()
    if not entity:
        entity = model(**{field_name: value})
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
    return entity


@with_relations("country", "genres", "actors", "languages")
async def create_movie(db: AsyncSession, movie: MovieCreate):

    duplicate = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    movie_data = movie.model_dump()
    if duplicate.scalar_one_or_none():
        from fastapi import HTTPException

        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data['name']}' and release date '{movie_data['date']}' already exists.",
        )

    db_genres = [
        await get_or_create(db, GenreModel, genre_name)
        for genre_name in movie_data.get("genres", [])
    ]

    db_actors = [
        await get_or_create(db, ActorModel, actor_name)
        for actor_name in movie_data.get("actors", [])
    ]

    db_languages = [
        await get_or_create(db, LanguageModel, language_name, field_name="name")
        for language_name in movie_data.get("languages", [])
    ]

    db_country = await get_or_create(
        db, CountryModel, movie_data.get("country"), field_name="code"
    )

    movie_data["actors"] = db_actors
    movie_data["genres"] = db_genres
    movie_data["languages"] = db_languages
    movie_data["country"] = db_country

    new_movie = MovieModel(**movie_data)
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return new_movie


async def get_movies(db: AsyncSession, page: int, per_page: int):
    total_movie = await db.execute(count(MovieModel.id))
    movies = await db.execute(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(desc(MovieModel.id))
    )

    return_movies = movies.scalars().all()
    total_movie = total_movie.scalar_one()
    total_pages = (total_movie + per_page - 1) // per_page

    return return_movies, page, total_movie, total_pages


@with_relations("country", "genres", "actors", "languages")
async def retrieve_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    return movie


@with_relations("country", "genres", "actors", "languages")
async def update_movie(db: AsyncSession, movie_data: dict, movie_id: int):
    movie = await retrieve_movie(db=db, movie_id=movie_id)

    print(f"movie is {movie}")

    if not movie:
        return None

    for key, value in movie_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    movie = await retrieve_movie(db=db, movie_id=movie_id)

    if not movie:
        return None

    await db.delete(movie)
    await db.commit()

    return movie
