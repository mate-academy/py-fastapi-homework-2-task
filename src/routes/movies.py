from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreate, MovieUpdateSchema
)
from crud.movies import (
    get_movies_list,
    create_movie,
    get_movie,
    delete_movie,
    update_movie,
    count_movies
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema, status_code=200)
async def movies_list(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    db_movies = await get_movies_list(db, page, per_page)

    total_items = await count_movies(db)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    return db_movies


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_new_movie(
        movie: MovieCreate,
        db: AsyncSession = Depends(get_db)
):
    movie = await create_movie(db, movie)
    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema, status_code=200)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await delete_movie(db, movie_id)


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie_by_id(
        movie_id: int,
        movie_update: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):

    return await update_movie(db, movie_id, movie_update)
