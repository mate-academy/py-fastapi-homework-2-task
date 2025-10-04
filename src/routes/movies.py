import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.requests import Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListItemSchema, MovieListResponseSchema, MovieDetailSchema
from schemas.errors import HTTP404ErrorSchema


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTP404ErrorSchema,
            "content": {
                "application/json": {
                    "example": HTTP404ErrorSchema(detail="No movies found."),
                },
            },
        },
    },
)
async def get_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    result = await db.execute(
        select(func.count())
        .select_from(MovieModel)
    )
    total_items = result.scalar_one_or_none()
    total_pages = math.ceil(total_items / per_page)
    print(total_pages)
    if not total_items or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    movies = await db.scalars(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return MovieListResponseSchema(
        movies=[
            MovieListItemSchema.model_validate(movie)
            for movie in movies
        ],
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTP404ErrorSchema,
            "content": {
                "application/json": {
                    "example": HTTP404ErrorSchema(
                        detail="Movie with the given ID was not found.",
                    ),
                },
            },
        },
    },
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return MovieDetailSchema.model_validate(movie)
