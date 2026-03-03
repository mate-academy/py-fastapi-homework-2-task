import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import Annotated
from starlette import status

import crud
import schemas
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()


# Write your code here
@router.get("/movies/", response_model=schemas.MovieListSchema)
async def read_movies(
        db: Annotated[AsyncSession, Depends(get_db)],
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20)
):

    db_movies = await crud.get_all_movies(
        db=db, offset=per_page * (page - 1), limit=per_page
    )
    if not db_movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await crud.get_amount_movies(db=db)
    total_pages = math.ceil(total_items / per_page)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": db_movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def get_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int
):
    db_movie = await crud.get_movie_by_id(db=db, movie_id=movie_id)
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return db_movie


@router.post(
    "/movies/",
    response_model=schemas.MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie: schemas.MovieCreateSchema
):
    try:
        db_movie = await crud.create_movie(db=db, movie=movie)
        return db_movie
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )


@router.patch("/movies/{movie_id}/", response_model=dict)
async def update_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int,
        movie_data: schemas.MovieUpdateSchema,
):
    db_movie = await crud.update_film(
        db=db,
        movie_id=movie_id,
        movie_data=movie_data
    )

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int
):
    db_movie = await crud.delete_movie(
        db=db,
        movie_id=movie_id
    )
    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
