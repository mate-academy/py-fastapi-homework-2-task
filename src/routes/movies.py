from math import ceil
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import ValidationError

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MessageSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()

# Write your code here
MOVIE_NOT_FOUND_MESSAGE = "Movie with the given ID was not found."
NO_MOVIES_FOUND_MESSAGE = "No movies found."
INVALID_INPUT_DATA_MESSAGE = "Invalid input data."
MOVIES_PATH_TEMPLATE = "/theater/movies/?page={page}&per_page={per_page}"
MOVIE_RELATIONS = (
    joinedload(MovieModel.country),
    joinedload(MovieModel.genres),
    joinedload(MovieModel.actors),
    joinedload(MovieModel.languages),
)


def _movie_details_query():
    return select(MovieModel).options(*MOVIE_RELATIONS)


def _build_page_link(page: int, per_page: int) -> str:
    return MOVIES_PATH_TEMPLATE.format(page=page, per_page=per_page)


def _raise_invalid_input_data() -> None:
    raise HTTPException(status_code=400, detail=INVALID_INPUT_DATA_MESSAGE)


def _validate_payload(schema_class, payload: dict[str, Any]):
    try:
        return schema_class.model_validate(payload)
    except ValidationError as error:
        raise HTTPException(
            status_code=400, detail=INVALID_INPUT_DATA_MESSAGE
        ) from error


async def _get_movie_or_404(movie_id: int, db: AsyncSession) -> MovieModel:
    result = await db.execute(_movie_details_query().where(MovieModel.id == movie_id))
    movie = result.unique().scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND_MESSAGE)
    return movie


async def _get_or_create_country(code: str, db: AsyncSession) -> CountryModel:
    result = await db.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalar_one_or_none()
    if country is not None:
        return country

    country = CountryModel(code=code, name=None)
    db.add(country)
    await db.flush()
    return country


async def _get_or_create_entities(
    model,
    values: list[str],
    field_name: str,
    db: AsyncSession,
) -> list[Any]:
    entities: list[Any] = []
    for value in values:
        result = await db.execute(
            select(model).where(getattr(model, field_name) == value)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            entity = model(**{field_name: value})
            db.add(entity)
            await db.flush()
        entities.append(entity)
    return entities


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail=NO_MOVIES_FOUND_MESSAGE)

    total_pages = ceil(total_items / per_page)
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail=NO_MOVIES_FOUND_MESSAGE)

    prev_page = _build_page_link(page - 1, per_page) if page > 1 else None
    next_page = _build_page_link(page + 1, per_page) if page < total_pages else None

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
    status_code=201,
)
async def create_movie(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    movie_data = _validate_payload(MovieCreateSchema, payload)

    existing_movie_result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if existing_movie_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    country = await _get_or_create_country(movie_data.country, db)
    genres = await _get_or_create_entities(GenreModel, movie_data.genres, "name", db)
    actors = await _get_or_create_entities(ActorModel, movie_data.actors, "name", db)
    languages = await _get_or_create_entities(
        LanguageModel, movie_data.languages, "name", db
    )

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
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        ) from error

    return await _get_movie_or_404(movie.id, db)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    return await _get_movie_or_404(movie_id, db)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    movie = await _get_movie_or_404(movie_id, db)
    await db.delete(movie)
    await db.commit()
    return Response(status_code=204)


@router.patch("/movies/{movie_id}/", response_model=MessageSchema)
async def update_movie(
    movie_id: int,
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> MessageSchema:
    movie_data = _validate_payload(MovieUpdateSchema, payload)
    movie = await _get_movie_or_404(movie_id, db)

    for field_name, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field_name, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        _raise_invalid_input_data()

    return MessageSchema(detail="Movie updated successfully.")
