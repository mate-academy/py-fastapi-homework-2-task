from datetime import timedelta, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import math
from database.crud import get_db, create_movie, get_movies, update_movie, delete_movie
from schemas import MovieCreate, MovieUpdate, MovieRead
from database.models import MovieModel

router = APIRouter()


@router.post("/movies/", response_model=MovieRead, status_code=201)
async def add_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    if len(movie.name) > 255:
        raise HTTPException(status_code=400, detail="Movie name must not exceed 255 characters")
    if movie.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Release date must not be more than one year in the future")
    if not (0 <= movie.score <= 100):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
    if movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Budget and revenue must be non-negative")

    existing_movie = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    ))
    if existing_movie.scalars().first():
        raise HTTPException(status_code=409, detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.")

    return await create_movie(db, movie)


@router.get("/movies/")
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    total_count = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = max(1, math.ceil(total_count / per_page))

    result = await db.execute(select(MovieModel).offset((page - 1) * per_page).limit(per_page))
    movies = result.scalars().all()

    return {
        "page": page,
        "per_page": per_page,
        "total": total_count,
        "total_pages": total_pages,
        "items": movies
    }


@router.get("/movies/{movie_id}", response_model=MovieRead)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movies(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.patch("/movies/{movie_id}", response_model=MovieRead)
async def edit_movie(movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)):
    existing_movie = await get_movies(db, movie_id)
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    duplicate_movie = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date,
        MovieModel.id != movie_id
    ))
    if duplicate_movie.scalars().first():
        raise HTTPException(status_code=409, detail="Movie with the same name and date already exists")

    return await update_movie(db, movie_id, movie)


@router.delete("/movies/{movie_id}", status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
