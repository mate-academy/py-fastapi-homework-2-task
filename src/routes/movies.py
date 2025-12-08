import math
from typing import List
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieModel
)
from src.schemas.movies import MovieList, MovieCreate, MovieDetail, MovieUpdate
from src.services.helpers import get_or_create_list

router = APIRouter()


@router.get("/movies/", response_model=List[MovieList])
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total_movies = await db.scalar(select(func.count())
                                   .select_from(MovieModel))
    if not total_movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = await db.execute(select(MovieModel)
                              .offset(offset)
                              .limit(per_page))
    movies = movies.scalars().all()
    total_pages = math.ceil(total_movies / per_page)
    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_movies,
    }


@router.post("/movies/", response_model=MovieDetail)
async def create_movie(
        movie: MovieCreate,
        db: AsyncSession = Depends(get_db)
):
    if movie.date > date.today() + timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Release date cannot be more than one year in the future."
        )

    country = select(CountryModel).where(
        CountryModel.code == movie.code.upper()
    )
    country = await db.scalar(country)
    if country is None:
        country = CountryModel(code=movie.code.upper())

    genres = await get_or_create_list(movie.genres, GenreModel, db)
    actors = await get_or_create_list(movie.actors, ActorModel, db)
    languages = await get_or_create_list(movie.languages, LanguageModel, db)

    created_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(created_movie)
    await db.commit()
    await db.refresh(created_movie)
    return created_movie


@router.get("/movies/{movie_id}", response_model=MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel)
                           .where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found.")
    return movie


@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(select(MovieModel)
                            .where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}")
async def patch_movie(
        movie_id: int,
        data: MovieUpdate,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(select(MovieModel)
                            .where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found.")
    try:
        for field, value in movie.items():
            setattr(movie, field, value)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    await db.commit()
    return {
        "detail": "Movie updated successfully.",
    }
