from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database.session_sqlite import get_sqlite_db
from src.database import crud
from src.schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreationRequestSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_sqlite_db),
):
    return await crud.get_movies_list(db, page, per_page)


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(
    movie_id: int,
    db: AsyncSession = Depends(get_sqlite_db),
):
    return await crud.get_movie_by_id(movie_id, db)


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    data: MovieCreationRequestSchema,
    db: AsyncSession = Depends(get_sqlite_db),
):
    return await crud.create_movie(db, data)


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    db: AsyncSession = Depends(get_sqlite_db),
):
    await crud.partial_movie_update(movie_id, db, payload)
    return {"detail": "Movie updated successfully."}


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_sqlite_db),
):
    await crud.delete_movie(movie_id, db)
    return None
