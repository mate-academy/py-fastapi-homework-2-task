import math
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    DetailMessageSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


router = APIRouter()

ModelType = TypeVar("ModelType", CountryModel, GenreModel, ActorModel, LanguageModel)

MOVIE_NOT_FOUND_MESSAGE = "Movie with the given ID was not found."
MOVIES_NOT_FOUND_MESSAGE = "No movies found."


async def get_or_create(
    db: AsyncSession,
    model: type[ModelType],
    field_name: str,
    value: str,
) -> ModelType:
    stmt = select(model).where(getattr(model, field_name) == value)
    result = await db.execute(stmt)
    instance = result.scalars().first()

    if instance:
        return instance

    instance = model(**{field_name: value})
    db.add(instance)
    await db.flush()
    return instance


async def get_movie_with_relations(
    db: AsyncSession,
    movie_id: int,
) -> MovieModel | None:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    return result.unique().scalars().first()


def get_duplicate_movie_message(name: str, release_date) -> str:
    return (
        f"A movie with the name '{name}' and release date "
        f"'{release_date}' already exists."
    )


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIES_NOT_FOUND_MESSAGE,
        )

    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIES_NOT_FOUND_MESSAGE,
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    duplicate_stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date,
    )
    duplicate_result = await db.execute(duplicate_stmt)
    duplicate_movie = duplicate_result.scalars().first()

    if duplicate_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_duplicate_movie_message(movie_data.name, movie_data.date),
        )

    country = await get_or_create(db, CountryModel, "code", movie_data.country)
    genres = [
        await get_or_create(db, GenreModel, "name", genre)
        for genre in movie_data.genres
    ]
    actors = [
        await get_or_create(db, ActorModel, "name", actor)
        for actor in movie_data.actors
    ]
    languages = [
        await get_or_create(db, LanguageModel, "name", language)
        for language in movie_data.languages
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
    db.add(movie)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_duplicate_movie_message(movie_data.name, movie_data.date),
        ) from exc

    created_movie = await get_movie_with_relations(db, movie.id)
    return created_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    movie = await get_movie_with_relations(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIE_NOT_FOUND_MESSAGE,
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIE_NOT_FOUND_MESSAGE,
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/movies/{movie_id}/",
    response_model=DetailMessageSchema,
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> DetailMessageSchema:
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIE_NOT_FOUND_MESSAGE,
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(movie, field_name, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    return DetailMessageSchema(detail="Movie updated successfully.")
