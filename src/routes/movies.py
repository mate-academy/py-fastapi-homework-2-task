import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status
from fastapi.responses import JSONResponse

from crud import movies as crud
from database import get_db
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieCreateSchema, MovieCreateResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
        db: AsyncSession = Depends(get_db)):
    movies = await crud.get_all_movies(db=db, page=page, per_page=per_page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found")

    count = await crud.get_count_movies(db=db)

    total_pages = math.ceil(count / per_page)

    response = {
        "movies": movies,
        "prev_page": (
            None
            if page == 1
            else f"/theater/movies/?page={page - 1}&per_page={per_page}"
        ),
        "next_page": (
            None
            if page >= total_pages
            else f"/theater/movies/?page={page + 1}&per_page={per_page}"
        ),
        "total_pages": total_pages,
        "total_items": count,
    }

    return response


@router.post("/movies/", response_model=MovieCreateResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    db_movie = await crud.get_movie_by_name_and_date(db=db, name=movie.name, date=movie.date)

    if db_movie:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"A movie with the name '{db_movie.name}' and release date '{db_movie.date}' already exists.")

    return await crud.create_movie(db=db, movie=movie)
