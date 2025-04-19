import datetime
import math
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

from crud import create_film, get_film, get_films
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieList, MovieDetail, MovieUpdate, MovieCreate

router = APIRouter()


@router.get("/movies", response_model=MovieModel)
async def get_movie_list(
    page: int = 1, per_page: int = 10, db: AsyncSession = Depends(get_db)
):
    if page < 1 or per_page < 1 or per_page > 20:
        raise HTTPException(status_code=404, detail="No movies found")
    if page == 1:
        prev_page_link = None
    else:
        prev_page_link = f"?page={page-1}&per_page={per_page}"


    movies = get_films(db)

    total_items = select(func.count(MovieModel.id))

    total_pages = math.ceil(total_items // per_page)

    if page == total_pages:
        next_page_link = None
    else:
        next_page_link = f"?{page + 1}=2&per_page={per_page}"

    response = MovieList(
        movies=[MovieDetail.from_orm(movie) for movie in movies],
        prev_page=prev_page_link,
        next_page=next_page_link,
        total_pages=total_pages,
        total_items=total_items,
    )

    return response


@router.post("/movies/", response_model=MovieDetail)
async def add_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    new_movie = await create_film(db, movie)
    search_if_exist = get_movie(new_movie.id, db)
    if new_movie.name in db and new_movie.date in search_if_exist:
        return HTTPException(
            status_code=409,
            detail=f"A movie with the name '{new_movie.name}' and release date '{new_movie.date}' already exists.",
        )

    if (new_movie.date.year > (datetime.date.today().year + 1) or
            new_movie.score < 0 or
            new_movie.score > 100 or
            new_movie.budget < 0 or
            new_movie.revenue < 0):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return new_movie


@router.get("/movies/{movie_id}", response_model=MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = get_film(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{film_id}", response_model=MovieDetail)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await delete_movie(movie_id, db)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.patch("/movies/{movie_id}", response_model=MovieDetail)
async def update_film(
    movie_id: int, movie: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    updated_movie = await update_film(movie_id, movie, db)

    if not updated_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    if updated_movie.score < 0 or updated_movie.score > 100 or updated_movie.budget < 0 or updated_movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")


    return HTTPException(200, detail="Movie updated successfully.")
