import math

from fastapi import Query, HTTPException
from sqlalchemy import func, select, desc
from sqlalchemy.orm import selectinload

from src.database import models
from src.database.session_sqlite import AsyncSQLiteSessionLocal
from src.schemas.movies import (
    MovieListResponseSchema,
    MovieCreationRequestSchema,
    MovieDetailSchema,
    MovieUpdateSchema
)
from src.database.crud_helpers import (
    get_or_create_country,
    get_or_create_by_name,
    unique_clean
)


async def get_movies_list(
        db: AsyncSQLiteSessionLocal,
        page: int,
        per_page: int
):
    count_stmt = select(func.count()).select_from(models.MovieModel)
    total_items = await db.scalar(count_stmt)

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    base = "/theater/movies/"
    prev_page = f"{base}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    offset = (page - 1) * per_page

    query = (
        select(models.MovieModel)
        .order_by(desc(models.MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def create_movie(db, payload: MovieCreationRequestSchema) -> MovieDetailSchema:
    stmt = select(models.MovieModel.id).where(
        models.MovieModel.name == payload.name,
        models.MovieModel.date == payload.date,
    )
    existing_id = await db.scalar(stmt)
    if existing_id is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date.isoformat()}' already exists."
        )

    country = await get_or_create_country(db, payload.country)

    genre_names = unique_clean(payload.genres)
    actor_names = unique_clean(payload.actors)
    language_names = unique_clean(payload.languages)

    genres = await get_or_create_by_name(db, models.GenreModel, genre_names)
    actors = await get_or_create_by_name(db, models.ActorModel, actor_names)
    languages = await get_or_create_by_name(db, models.LanguageModel, language_names)

    movie = models.MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country_id=country.id,
    )

    # link relations
    movie.genres = genres
    movie.actors = actors
    movie.languages = languages

    db.add(movie)

    await db.flush()

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
    movie_full = await db.scalar(stmt)
    return movie_full


async def get_movie_by_id(movie_id: int, db: AsyncSQLiteSessionLocal):
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

    movie = await db.scalar(stmt)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


async def delete_movie(movie_id: int, db: AsyncSQLiteSessionLocal):
    stmt = select(models.MovieModel).where(models.MovieModel.id == movie_id)
    result = await db.scalar(stmt)

    if result is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(result)


async def partial_movie_update(
        movie_id: int,
        db: AsyncSQLiteSessionLocal,
        payload: MovieUpdateSchema
):
    query = select(models.MovieModel).where(models.MovieModel.id == movie_id)
    movie_to_update = await db.scalar(query)

    if movie_to_update is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie_to_update, field, value)
