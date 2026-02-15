from typing import Annotated

from fastapi import status
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crud import movies as crud
from database import get_db
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageResponseSchema
)

SessionDep = Annotated[AsyncSession, Depends(get_db)]
router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    summary="List movies",
)
async def list_movies(
    db: SessionDep,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    movies, total_items = await crud.get_movies_paginated(
        db,
        page=page,
        per_page=per_page,
    )

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page

    prev_page = (
        f"/api/v1/theater/movies/?page={page-1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"/api/v1/theater/movies/?page={page+1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie",
)
async def create_movie(
    db: SessionDep,
    data: MovieCreateSchema,
):
    existing = await crud.get_movie_by_name_and_date(
        db,
        data.name,
        data.date,
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{data.name}' "
                   f"and release date '{data.date}' already exists."
        )

    try:
        movie = await crud.create_movie(db, data)
        return movie
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    summary="Get movie by ID",
)
async def get_movie(
    db: SessionDep,
    movie_id: int,
):
    movie = await crud.get_movie_by_id(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete movie by ID",
)
async def delete_movie(
    db: SessionDep,
    movie_id: int,
):
    movie = await crud.get_movie_by_id(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await crud.delete_movie(db, movie)


@router.patch(
    "/movies/{movie_id}/",
    response_model=MessageResponseSchema,
    summary="Update movie by ID",
)
async def update_movie(
    db: SessionDep,
    movie_id: int,
    data: MovieUpdateSchema,
):
    movie = await crud.get_movie_by_id(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    try:
        await crud.update_movie(db, movie, data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )

    return {"detail": "Movie updated successfully."}
