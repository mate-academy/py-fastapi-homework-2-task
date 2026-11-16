from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


router = APIRouter()

NOT_FOUND_DETAIL = "Movie with the given ID was not found."


def _movie_details_statement():
    return select(MovieModel).options(
        joinedload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    )


async def _get_or_create_named_entity(
    db: AsyncSession,
    model: Any,
    name: str,
) -> Any:
    result = await db.execute(select(model).where(model.name == name))
    entity = result.scalar_one_or_none()
    if entity is None:
        entity = model(name=name)
        db.add(entity)
    return entity


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    payload: Any = Body(...),
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    try:
        movie_data = MovieCreateSchema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    duplicate_result = await db.execute(
        select(MovieModel.id).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if duplicate_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date.isoformat()}' already exists."
            ),
        )

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.code == movie_data.country)
    )
    country = country_result.scalar_one_or_none()
    if country is None:
        country = CountryModel(code=movie_data.country)
        db.add(country)

    genres = [
        await _get_or_create_named_entity(db, GenreModel, name)
        for name in dict.fromkeys(movie_data.genres)
    ]
    actors = [
        await _get_or_create_named_entity(db, ActorModel, name)
        for name in dict.fromkeys(movie_data.actors)
    ]
    languages = [
        await _get_or_create_named_entity(db, LanguageModel, name)
        for name in dict.fromkeys(movie_data.languages)
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
        duplicate_result = await db.execute(
            select(MovieModel.id).where(
                MovieModel.name == movie_data.name,
                MovieModel.date == movie_data.date,
            )
        )
        if duplicate_result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A movie with the name '{movie_data.name}' and release date "
                    f"'{movie_data.date.isoformat()}' already exists."
                ),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    result = await db.execute(
        _movie_details_statement().where(MovieModel.id == movie.id)
    )
    return result.scalar_one()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    result = await db.execute(
        _movie_details_statement().where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_DETAIL,
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_DETAIL,
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    payload: Any = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        update_data = MovieUpdateSchema.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_DETAIL,
        )

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from exc

    return {"detail": "Movie updated successfully."}
