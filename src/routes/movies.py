from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud import movies
from database import get_db
from schemas.movies import MovieCreateSchema, MovieListResponseSchema, MovieDetailSchema, MovieUpdate

router = APIRouter(
    prefix="/movies",
    tags=["movies"]
)

@router.get("/", response_model=MovieListResponseSchema, status_code=status.HTTP_200_OK)
async def list_movies(
        request: Request,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
        db: AsyncSession = Depends(get_db)
):
    movies_, total_items = await movies.get_movies_paginated(db, page, per_page)

    total_pages = ceil(total_items / per_page) if total_items > 0 else 1

    base_url = str(request.url.path).replace("/api/v1", "").split('?')[0]

    if not movies_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    def create_link(p: int):
        return f"{base_url}?page={p}&per_page={per_page}"

    return {
        "movies": movies_,
        "total_items": total_items,
        "total_pages": total_pages,
        "prev_page": create_link(page - 1) if page > 1 else None,
        "next_page": create_link(page + 1) if page < total_pages else None
    }


@router.get("/{movie_id}/", response_model=MovieDetailSchema, status_code=status.HTTP_200_OK)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await movies.get_movie_by_id(db, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie",
    description="Creates a new movie with automatic entity linking. Returns 409 if duplicate exists."
)
async def create_movie(movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    return await movies.create_movie(db=db, movie_in=movie_in)


@router.delete(
    "/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a movie",
    description="Deletes a specific movie by its ID."
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    deleted_movie = await movies.delete_movie(db, movie_id)

    if deleted_movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return None


@router.patch(
    "/{movie_id}/",
    status_code=status.HTTP_200_OK,
    summary="Update movie details",
    description="Partially updates movie details. Returns 404 if not found."
)
async def update_movie(
        movie_id: int,
        movie_update: MovieUpdate,
        db: AsyncSession = Depends(get_db)
):
    updated_movie = await movies.update_movie(db, movie_id, movie_update)

    if not updated_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return {"detail": "Movie updated successfully."}
