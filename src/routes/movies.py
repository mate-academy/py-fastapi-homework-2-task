from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

from crud import get_all_movies_paginated, get_movie, create_movie
from database import get_db, MovieModel
from database.models import LanguageModel, ActorModel, GenreModel, CountryModel
from schemas import MovieDetailSchema, MovieListResponseSchema
from schemas.movies import MovieCreateSchema

router = APIRouter()


@router.get("/movies/{movie_id}/")
async def retrieve_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(movie_id, db)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_list_of_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(ge=1, default=1),
        per_page: int = Query(ge=1, le=20, default=10)
):
    response = await get_all_movies_paginated(db, page, per_page)

    if not response["movies"]:
        raise HTTPException(status_code=404, detail="No movies found.")

    return response


@router.post("/movies/", response_model=MovieDetailSchema)
async def add_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    return await create_movie(movie, db)
