from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieAddSchema,
    MovieUpdateSchema,
)
from crud.movies import (
    read_all_movies,
    create_movie,
    AlreadyExists,
    read_one_movie,
    delete_movie,
    update_movie,
)

router = APIRouter()


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=20)


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    pagination_params: Annotated[PaginationParams, Query()],
    db: AsyncSession = Depends(get_db),
):
    skip = (pagination_params.page - 1) * pagination_params.per_page
    movies, total_items = await read_all_movies(
        db, skip=skip, limit=pagination_params.per_page
    )
    movies = [MovieListItemSchema.model_validate(movie) for movie in movies]
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = total_items // pagination_params.per_page
    if total_items % pagination_params.per_page != 0:
        total_pages += 1

    url = "/theater/movies/"
    next_page = (
        url
        + f"?page={pagination_params.page + 1}&per_page={pagination_params.per_page}"
        if pagination_params.page < total_pages
        else None
    )
    prev_page = (
        url
        + f"?page={pagination_params.page - 1}&per_page={pagination_params.per_page}"
        if pagination_params.page > 1
        else None
    )
    result = MovieListResponseSchema(
        movies=movies,
        total_pages=total_pages,
        total_items=total_items,
        next_page=next_page,
        prev_page=prev_page,
    )
    return result


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_new_movie(
    movie: MovieAddSchema,
    db: AsyncSession = Depends(get_db),
):
    try:
        response_movie = await create_movie(db, movie)
        return response_movie
    except AlreadyExists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await read_one_movie(db, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_rows = await delete_movie(db, movie_id)
    if deleted_rows != 1:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return


@router.patch("/movies/{movie_id}/")
async def change_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    updated_rows = await update_movie(db, movie_id, movie)
    if updated_rows != 1:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return {"detail": "Movie updated successfully."}
