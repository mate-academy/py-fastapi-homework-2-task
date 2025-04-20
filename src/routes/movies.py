from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieCreateSchema,
    MovieReadSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    MovieReadPaginatedSchemas,

    PaginationQuerySchema
)
from crud.movies_crud import (
    create_movies,
    read_movies,
    read_movie,
    remove_movie,
    update_movie
)
from paginations import get_paginated_response


router = APIRouter()


@router.get("/movies/", response_model=MovieReadPaginatedSchemas)
async def get_movies(q: Annotated[PaginationQuerySchema, Query()], db: AsyncSession = Depends(get_db)):
    movies = await read_movies(db, q.page, q.per_page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return {
        "movies": movies,
        ** await get_paginated_response(
            query=select(MovieModel),
            db=db, page=q.page, per_page=q.per_page,
            url_path="/theater/movies/"
        )
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_film(film: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    return await create_movies(movie=film, db=db)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def detail_movie(
        movie_id: int, db: AsyncSession = Depends(get_db)
):
    movie = await read_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            detail="Movie with the given ID was not found.",
            status_code=404
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await remove_movie(movie_id=movie_id, db=db)
    if not movie:
        raise HTTPException(
            detail="Movie with the given ID was not found.",
            status_code=404
        )


@router.patch("/movies/{movie_id}/", status_code=200)
async def patch_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await update_movie(movie_id=movie_id, db=db, movie_sch=movie)
    if not movie:
        raise HTTPException(
            detail="Movie with the given ID was not found.",
            status_code=404
        )
    return {"detail": "Movie updated successfully."}
