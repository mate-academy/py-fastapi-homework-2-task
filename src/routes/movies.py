import datetime
from http.client import HTTPResponse

from django.core.exceptions import BadRequest
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.openapi.models import Response
from rest_framework.exceptions import NotFound
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, Session
from starlette.responses import JSONResponse
from werkzeug.exceptions import Conflict

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieList, MovieDetail, MovieUpdate, MovieCreate

router = APIRouter()


@router.post("/movies", response_model=MovieModel)
async def get_movie_list(
    page: int = 1, per_page: int = 10, db: AsyncSession = Depends(get_db)
):
    if page < 1 or per_page < 1 or per_page > 20:
        raise HTTPException(status_code=404, detail="No moview found")
    if page == 1:
        prev_page_link = None
    else:
        prev_page_link = f"/theater/movies/?{page - 1}=2&per_page={per_page}"

    query = select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    total_items = (await db.execute(query)).scalar()

    total_pages = total_items // per_page

    if total_items % per_page != 0:
        total_pages += 1

    if page == total_pages:
        next_page_link = None
    else:
        next_page_link = f"/theater/movies/?{page + 1}=2&per_page={per_page}"

    response = MovieList(
        movies=[MovieDetail.from_orm(movie) for movie in movies],
        prev_page=prev_page_link,
        next_page=next_page_link,
        total_pages=total_pages,
        total_items=total_items,
    )

    return response


@router.post("/movies/", response_model=MovieCreate)
async def add_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = MovieModel(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=movie.country_id,
        country=movie.country,
        genres=movie.genres,
        actors=movie.actors,
        languages=movie.languages,
    )
    if new_movie.date.year > (datetime.date().year + 1):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if new_movie.name in db and new_movie.date in db:
        return HTTPException(
            status_code=409,
            detail=f"A movie with the name '{new_movie.name}' and release date '{new_movie.date}' already exists.",
        )

    return new_movie


@router.get("/movies/{film_id}", response_model=MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{film_id}", response_model=MovieDetail)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    db.commit()
    return movie


@router.patch("/movies/{movie_id}", response_model=MovieUpdate)
async def update_film(
    movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    updated_movie = result.scalar_one_or_none()

    if not updated_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    updated_movie = MovieModel(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=movie.country_id,
        country=movie.country,
        genres=movie.genres,
        actors=movie.actors,
        languages=movie.languages,
    )

    return updated_movie
