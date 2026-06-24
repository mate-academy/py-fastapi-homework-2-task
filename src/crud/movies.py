import math

from fastapi import Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from starlette import status

import schemas
from database import models
from database.dependencies import DBDep


async def get_all_movies(
    db: DBDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
) -> tuple[list[models.MovieModel], int, int]:
    offset_value = (page - 1) * per_page

    total_items = 0
    try:
        count_result = await db.scalar(select(func.count()).select_from(models.MovieModel))
        total_items = int(count_result) if count_result else 0
    except Exception as e:
        print(f"Error counting movies: {e}")
        total_items = 0

    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0

    movies = []
    if total_items > 0:
        try:
            result = await db.execute(
                select(models.MovieModel)
                .order_by(models.MovieModel.id.desc())
                .offset(offset_value)
                .limit(per_page)
            )
            movies = list(result.scalars().all())
        except Exception as e:
            print(f"Error fetching movies: {e}")
            movies = []

    return movies, total_items, total_pages


async def create_movie(
    movie_data: schemas.MovieCreateRequestSchema,
    db: DBDep
) -> models.MovieModel | None:
    duplicate_stmt = select(models.MovieModel).where(
        models.MovieModel.name == movie_data.name,
        models.MovieModel.date == movie_data.date
    )
    existing_movie = await db.scalar(duplicate_stmt)

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country, _ = await models.CountryModel.get_or_create(
        session=db,
        code=movie_data.country,
        defaults={"name": None}
    )

    genres_list = []
    for genre_name in movie_data.genres:
        genre, _ = await models.GenreModel.get_or_create(session=db, name=genre_name)
        genres_list.append(genre)

    actors_list = []
    for actor_name in movie_data.actors:
        actor, _ = await models.ActorModel.get_or_create(session=db, name=actor_name)
        actors_list.append(actor)

    languages_list = []
    for lang_name in movie_data.languages:
        language, _ = await models.LanguageModel.get_or_create(session=db, name=lang_name)
        languages_list.append(language)

    movie_fields = movie_data.model_dump(exclude={"country", "genres", "actors", "languages"})

    movie = models.MovieModel(
        **movie_fields,
        country=country,
        genres=genres_list,
        actors=actors_list,
        languages=languages_list
    )

    db.add(movie)
    await db.flush()
    await db.commit()

    stmt = (
        select(models.MovieModel)
        .where(models.MovieModel.id == movie.id)
        .options(
            selectinload(models.MovieModel.country),
            selectinload(models.MovieModel.genres),
            selectinload(models.MovieModel.actors),
            selectinload(models.MovieModel.languages),
        )
    )
    refreshed_movie = await db.scalar(stmt)

    return refreshed_movie


async def get_movie_by_id(
    movie_id: int,
    db: DBDep
) -> models.MovieModel | None:
    stmt = (
        select(models.MovieModel)
        .where(models.MovieModel.id == movie_id)
        .options(
            selectinload(models.MovieModel.country),
            selectinload(models.MovieModel.genres),
            selectinload(models.MovieModel.actors),
            selectinload(models.MovieModel.languages),
        )
    )
    return await db.scalar(stmt)


async def delete_movie(db: DBDep, movie: models.MovieModel) -> None:
    await db.delete(movie)
    await db.commit()


async def patch_movie_fields(
    db: DBDep,
    movie: models.MovieModel,
    movie_update: schemas.MovieUpdateRequestSchema
) -> models.MovieModel:
    update_data = movie_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.flush()
    await db.commit()
    await db.refresh(movie)
    return movie
