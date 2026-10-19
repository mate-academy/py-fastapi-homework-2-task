from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from starlette import status
from database import get_db
from database.models import MovieModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateRequestSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
)
import crud.movies
import crud.common

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    per_page: Annotated[int, Query(ge=1, le=20, description="Items per page")] = 10,
):
    skip = (page - 1) * per_page
    movies = await crud.movies.get_movies(db=db, skip=skip, limit=per_page)

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )
    total_items = await crud.common.count_items(db=db, model=MovieModel)
    total_pages = (total_items + per_page - 1) // per_page
    return MovieListResponseSchema(
        movies=movies,
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    data: MovieCreateRequestSchema,
):
    name = data.name
    date = data.date
    movie = await crud.movies.get_movie_by_name_date(db=db, name=name, date=date)
    if movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{name}' "
            f"and release date '{date}' already exists.",
        )
    try:
        return await crud.movies.create_movie(db, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(db: Annotated[AsyncSession, Depends(get_db)], movie_id: int):
    movie = await crud.movies.get_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(db: Annotated[AsyncSession, Depends(get_db)], movie_id: int):
    movie = await crud.movies.get_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    await crud.movies.delete_movie(db=db, movie=movie)


@router.patch("/movies/{movie_id}/")
async def partial_update_movie(
    db: Annotated[AsyncSession, Depends(get_db)], movie_id: int, data: MovieUpdateSchema
):
    movie = await crud.movies.get_movie(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    try:
        await crud.movies.update_movie(db=db, movie=movie, data=data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    return {"detail": "Movie updated successfully."}
