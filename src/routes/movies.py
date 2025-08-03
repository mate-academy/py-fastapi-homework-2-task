from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from starlette import status
from starlette.responses import Response, JSONResponse

from crud import get_movies, get_movie, create_movie, update_movie, delete_movie
from schemas.movies import MovieRead, MovieCreate, MovieUpdate, MovieList

router = APIRouter()


@router.get("/movies/", response_model=MovieList)
async def list_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
):
    movies, total_items = await get_movies(db, page, per_page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieList(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
async def add_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = await create_movie(db, movie)
    return new_movie


@router.get("/movies/{movie_id}/", response_model=MovieRead)
async def detail_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.patch("/movies/{movie_id}/")
async def edit_movie(movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)):
    updated_movie = await update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return JSONResponse(status_code=200, content={"detail": "Movie updated successfully."})


@router.delete("/movies/{movie_id}/", status_code=204)
async def destroy_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return Response(status_code=204)
