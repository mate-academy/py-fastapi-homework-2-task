from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.crud import (
    read_movies_paginated,
    create_movie,
    read_movie,
    update_movie,
    delete_movie
)
from schemas.movies import MovieRead, MovieCreate, MovieUpdate, MovieList


router = APIRouter()


@router.get("/movies/", response_model=MovieList)
async def get_movies_list_view(
    page: int = Query(1, ge=1, description="The page number."),
    per_page: int = Query(10, ge=1, le=20, description="Number of movies per page."),
    db: AsyncSession = Depends(get_db)
):
    movies, total_movies = await read_movies_paginated(db, page, per_page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_movies + per_page - 1) // per_page

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MovieList(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_movies
    )


@router.post("/movies/", response_model=MovieRead, status_code=201)
async def create_movie_view(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = await create_movie(db, movie)
    return new_movie


@router.get("/movies/{movie_id}/", response_model=MovieRead)
async def get_movie_view(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await read_movie(db, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.patch("/movies/{movie_id}/", response_model=MovieRead)
async def update_movie_view(movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)):
    updated_movie = await update_movie(db, movie_id, movie)

    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return JSONResponse(status_code=200, content={"detail": "Movie updated successfully."})


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_view(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_movie = await delete_movie(db, movie_id)

    if not deleted_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
