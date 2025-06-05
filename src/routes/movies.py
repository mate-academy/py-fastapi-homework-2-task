from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crud.movies import delete_movie, create_movie
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import PaginatedMoviesResponseSchema, MovieDetailSchema, MovieCreateSchema
from crud import get_movies, get_movie_by_id, update_movie_by_id
from schemas.movies import MovieResponseSchema, MovieUpdate

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


@router.post("/movies/", response_model=MovieResponseSchema, status_code=201)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    db_movie = await create_movie(db, movie)

    return {
        "id": db_movie.id,
        "name": db_movie.name,
        "date": db_movie.date,
        "score": db_movie.score,
        "overview": db_movie.overview,
        "status": db_movie.status,
        "budget": db_movie.budget,
        "revenue": db_movie.revenue,
        "country": db_movie.country.name,
        "genres": [g.name for g in db_movie.genres],
        "actors": [a.name for a in db_movie.actors],
        "languages": [lang.name for lang in db_movie.languages],
    }


@router.delete("/movies/{movie_id}/", status_code=204)
async def del_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    await delete_movie(db, movie_id)


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
    summary="Update a movie by ID",
    response_model=dict,
    responses={
        200: {"description": "Movie updated successfully."},
        404: {"description": "Movie not found."},
        400: {"description": "Invalid input data."}
    }
)
async def update_movie(
    movie_id: int,
    movie_update: MovieUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_movie = await update_movie_by_id(movie_id, movie_update, db)
    return db_movie
