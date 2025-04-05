from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud.movies import (
    get_movies_paginated,
    create_movie,
    get_movie_by_id,
    update_movie,
    delete_movie
)
from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema
)
from utils.pagination import (
    get_total_items,
    get_paginated_items,
    get_pagination_links
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
) -> MovieListResponseSchema:
    response = await get_movies_paginated(db, page, per_page)
    return MovieListResponseSchema(**response)


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie_endpoint(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    new_movie = await create_movie(db, movie)
    return MovieDetailSchema.model_validate(new_movie)


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    return await get_movie_by_id(db, movie_id)


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie_endpoint(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    await delete_movie(db, movie_id)


@router.patch("/{movie_id}", response_model=dict)
async def update_movie_endpoint(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    await update_movie(db, movie_id, movie)
    return {"detail": "Movie updated successfully."}
