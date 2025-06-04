from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import PaginatedMoviesResponseSchema, MovieDetailSchema, MovieCreateSchema
from crud import get_movies, get_movie_by_id, create_movie

router = APIRouter()

@router.get("/movies/", response_model=PaginatedMoviesResponseSchema)
async def list_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100)
):
    movies = await get_movies(db, page, per_page)

    if not movies["movies"]:
        raise HTTPException(status_code=404, detail="No movies found.")

    return movies


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def detail_movie(db: AsyncSession = Depends(get_db), movie_id: int = 1):
    movie = await get_movie_by_id(db, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.post("/movies/", response_model=MovieCreateSchema)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    movie = await create_movie(db, movie)

    return movie