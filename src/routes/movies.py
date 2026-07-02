import math
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    LanguageModel,
    ActorModel,
    GenreModel
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreate,
    MovieDetailSchema,
    MovieUpdate,
)

router = APIRouter()

ModelT = TypeVar("ModelT", CountryModel, LanguageModel, ActorModel, GenreModel)


async def _get_or_create(db: AsyncSession, model, field_name, value):
    result = await db.execute(select(model).where(getattr(model, field_name) == value))
    instance = result.scalar_one_or_none()
    if instance:
        return instance
    instance = model(**{field_name: value})
    db.add(instance)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        result = await db.execute(
            select(model).where(getattr(model, field_name) == value)
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            raise

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


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    stmt = (
        select(MovieModel).offset(offset).limit(per_page).order_by(MovieModel.id.desc())
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar_one()
    total_pages = math.ceil(total_items / per_page)

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
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


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(data: MovieCreate, db: AsyncSession = Depends(get_db)):
    # Duplicate check
    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == data.name,
            MovieModel.date == data.date,
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists.",
        )

    # Entity linking
    country = await _get_or_create(db, CountryModel, "code", data.country)
    genres = [
        await _get_or_create(db, GenreModel, "name", genre) for genre in data.genres
    ]
    actors = [
        await _get_or_create(db, ActorModel, "name", actor) for actor in data.actors
    ]
    languages = [
        await _get_or_create(db, LanguageModel, "name", language)
        for language in data.languages
    ]

    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    movie = await get_movie_with_relations(db, movie.id)
    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_with_relations(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    db_result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = db_result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
    movie_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    db_result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = db_result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    try:
        update_schema = MovieUpdate.model_validate(data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    update_data = update_schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
