from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_bd
from src.schemas.movies import MovieListResponse, MovieCreate, MovieDetail, MovieUpdate
from src.crud import create_movie, get_movie, get_movies, update_movie, delete_movie

router = APIRouter()


@router.post("/movies/", response_model=MovieDetail, status_code=201)
async def add_movie(movie: MovieCreate, db: AsyncSession = Depends(get_bd)):
    new_movie = await create_movie(db, movie)
    return new_movie


@router.get("/movies/", response_model=MovieListResponse)
async def list_movies(db: AsyncSession = Depends(get_bd),
                      page: int = Query(1, ge=1),
                      per_page: int = Query(10, ge=1, le=20)
                      ):
    movies = await get_movies(db, page, per_page)
    return movies


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_bd)):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.patch("/movies/{movie_id}/", response_model=MovieDetail)
async def edit_movie(movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_bd)):
    updated_movie = await update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return {"message": "Movie updated successfully.", "movie": updated_movie}


@router.delete("/movies/{movie_id}/", response_model=MovieDetail, status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_bd)):
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return deleted_movie
