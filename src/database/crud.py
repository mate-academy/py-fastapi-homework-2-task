from datetime import date
from typing import List

import pycountry
from fastapi import HTTPException
from sqlalchemy import select, func, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

from database import MovieModel
from database.models import CountryModel, GenreModel, LanguageModel, ActorModel
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def get_movies(db: AsyncSession, limit: int = 10, offset: int = 0) -> List[MovieModel]:
    stm = select(MovieModel).limit(limit).offset(offset).order_by(MovieModel.id.desc())

    results = await db.scalars(stm)

    results = list(results)

    if len(results) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    return results


async def get_movies_count(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(MovieModel)
    result = await db.execute(stmt)

    return result.scalar() or 0


async def get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel:
    result = await db.get(
        MovieModel,
        movie_id,
        options=[
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.actors)
        ]
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return result


async def get_or_create_country_by_code(db: AsyncSession, country_code: str) -> CountryModel:
    stmt = select(CountryModel).where(CountryModel.code == country_code)
    result = await db.scalar(stmt)

    if len(country_code) == 2:
        country_name = pycountry.countries.get(alpha_2=country_code).name
    else:
        country_name = pycountry.countries.get(alpha_3=country_code).name

    if not result:
        result = CountryModel(
            code=country_code,
            name=country_name,
        )

        db.add(result)
        await db.flush()
        await db.refresh(result)

    return result


async def get_or_create_model_from_list_with_names(db: AsyncSession, model, names: List[str]) -> List:
    names = set(names)

    stmt = select(model).where(model.name.in_(names))

    existing_objs = await db.scalars(stmt)
    existing_objs = list(existing_objs)

    existing_names = {
        result.name
        for result in existing_objs
        if result.name in names
    }

    names_to_create = [
        {"name": name}
        for name in names
        if name not in existing_names
    ]

    new_objs = []

    if len(names_to_create) > 0:
        insert_stmt = insert(model).values(names_to_create).returning(model)
        new_results = await db.execute(insert_stmt)
        new_objs = list(new_results.scalars())

        await db.flush()

    return existing_objs + new_objs


async def movie_with_name_and_date(db: AsyncSession, movie: str, date: date) -> MovieModel:
    stmt = select(MovieModel).where(
        MovieModel.name == movie,
        MovieModel.date == date
    )
    result = await db.scalar(stmt)

    return result


async def create_movie(db: AsyncSession, movie: MovieCreateSchema) -> MovieModel:
    try:
        movie_check = await movie_with_name_and_date(db, movie.name, movie.date)
        if movie_check:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A movie with the name '{movie_check.name}' and "
                    f"release date '{movie_check.date}' already exists."
                )
            )

        country = await get_or_create_country_by_code(db, movie.country)
        genres = await get_or_create_model_from_list_with_names(db, GenreModel, movie.genres)
        actors = await get_or_create_model_from_list_with_names(db, ActorModel, movie.actors)
        languages = await get_or_create_model_from_list_with_names(db, LanguageModel, movie.languages)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."

        )

    new_movie_params = movie.model_dump()

    new_movie_params["country"] = country
    new_movie_params["genres"] = genres
    new_movie_params["actors"] = actors
    new_movie_params["languages"] = languages

    new_movie = MovieModel(**new_movie_params)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    db.expunge(new_movie)

    return await get_movie_by_id(db, new_movie.id)


async def delete_movie(db: AsyncSession, movie_id: int) -> None:
    await get_movie_by_id(db, movie_id)

    stmt = delete(MovieModel).where(MovieModel.id == movie_id)

    await db.execute(stmt)
    await db.commit()


async def update_movie(db: AsyncSession, movie_id: int, movie_in: MovieUpdateSchema) -> MovieModel:
    db_movie = await get_movie_by_id(db, movie_id)

    update_data = movie_in.model_dump(exclude_unset=True)

    try:
        if "country" in update_data:
            country_code = update_data.pop("country")
            db_movie.country = await get_or_create_country_by_code(db, country_code)

        if "genres" in update_data:
            genre_names = update_data.pop("genres")
            db_movie.genres = await get_or_create_model_from_list_with_names(db, GenreModel, genre_names)

        if "actors" in update_data:
            actor_names = update_data.pop("actors")
            db_movie.actors = await get_or_create_model_from_list_with_names(db, ActorModel, actor_names)

        if "languages" in update_data:
            language_names = update_data.pop("languages")
            db_movie.languages = await get_or_create_model_from_list_with_names(db, LanguageModel, language_names)

        for key, value in update_data.items():
            setattr(db_movie, key, value)

    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )

    db.add(db_movie)
    await db.commit()

    return await get_movie_by_id(db, movie_id)
