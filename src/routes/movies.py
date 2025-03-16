from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from routes.crud import (
    create_movie,
    delete_movie,
    get_movie,
    get_movies,
    update_movie,
)
from schemas.movies import (
    MovieCreate,
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieUpdate,
)


router = APIRouter()


# Write your code here
@router.get("/movies", response_model=MovieListResponseSchema)
async def list_movies(
    db: AsyncSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    total_items_result = await db.execute(
        select(func.count()).select_from(MovieModel)
    )
    total_items = total_items_result.scalar()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)

    movies = await get_movies(db)

    prev_page = (
        f"/movies?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/movies?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies", response_model=MovieDetailSchema)
async def add_movie(db: AsyncSession, movie: MovieCreate):
    old_movie_result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    old_movie = old_movie_result.scalar_one_or_none()
    if old_movie is not None:
        raise HTTPException(
            status_code=409,
            detail="A movie with the name '{name}' and release date '{date}' already exists.",
        )
    new_movie = await create_movie(db, movie)
    return new_movie


@router.get("/movies/{movie_id}", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = get_movie(movie_id, db)
    return movie


@router.delete("/movies/{movie_id}")
async def destroy_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await delete_movie(db, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.patch("/movies/{movie_id}", response_model=MovieDetailSchema)
async def edit_movie(
    movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    movie = await update_movie(db, movie_id, movie)
    return movie
