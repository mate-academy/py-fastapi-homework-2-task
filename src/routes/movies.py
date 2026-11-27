import json
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import MovieModel, get_db
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


async def _parse_json_object(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    if not raw_body or not raw_body.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )
    try:
        payload = json.loads(raw_body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )
    return payload


def _movie_detail_query():
    return select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    )


async def _get_or_create_named(
    db: AsyncSession, model_cls, name: str
):
    clean_name = name.strip()
    stmt = select(model_cls).where(model_cls.name == clean_name)
    obj = await db.scalar(stmt)
    if obj is None:
        obj = model_cls(name=clean_name)
        db.add(obj)
        await db.flush()
    return obj


async def _get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    clean_code = code.strip().upper()
    stmt = select(CountryModel).where(CountryModel.code == clean_code)
    country = await db.scalar(stmt)
    if country is None:
        country = CountryModel(code=clean_code)
        db.add(country)
        await db.flush()
    return country


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id))) or 0
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0

    if total_items == 0 or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    offset = (page - 1) * per_page
    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = list((await db.scalars(stmt)).all())

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await _parse_json_object(request)
    try:
        movie_data = MovieCreateSchema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    existing_stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date,
    )
    if await db.scalar(existing_stmt) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    country = await _get_or_create_country(db, movie_data.country)
    genres = [
        await _get_or_create_named(db, GenreModel, g) for g in movie_data.genres
    ]
    actors = [
        await _get_or_create_named(db, ActorModel, a) for a in movie_data.actors
    ]
    languages = [
        await _get_or_create_named(db, LanguageModel, l)
        for l in movie_data.languages
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
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        ) from exc

    created_movie = await db.scalar(
        _movie_detail_query().where(MovieModel.id == movie.id)
    )
    return MovieDetailSchema.model_validate(created_movie)


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(
        _movie_detail_query().where(MovieModel.id == movie_id)
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return MovieDetailSchema.model_validate(movie)


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await _parse_json_object(request)
    try:
        movie_data = MovieUpdateSchema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    movie = await db.scalar(
        _movie_detail_query().where(MovieModel.id == movie_id)
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    updates = movie_data.model_dump(exclude_unset=True)
    target_name = updates.get("name", movie.name)
    target_date = updates.get("date", movie.date)

    for field, value in updates.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{target_name}' "
                f"and release date '{target_date}' already exists."
            ),
        ) from exc

    return {"detail": "Movie updated successfully."}


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()
