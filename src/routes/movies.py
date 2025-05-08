from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from crud import get_movies, get_movie, create_movie, update_movie, delete_movie
from database import get_db
from schemas import MovieDetailResponseSchema
from schemas.movies import MovieCreate, MovieUpdate, MovieRead

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def list_movies(
    per_page: int = Query(10, ge=1, le=20),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    movies = await get_movies(per_page=per_page, page=page, db=db)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return movies


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def once_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie(movie_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_film(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = await create_movie(movie, db)
    return new_movie


@router.patch("/movies/{movie_id}/", response_model=dict)
async def edit_movie(movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)):
    updated_movie = await update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return deleted_movie
