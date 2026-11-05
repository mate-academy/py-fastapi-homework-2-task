from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import schemas
from crud.movies import (
    get_all_movies,
    create_movie_db,
    get_movie_by_name_and_date,
    patch_movie,
)
from database import get_db, MovieModel


router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_movies_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    total_items = (
        await db.scalar(select(func.count()).select_from(MovieModel)) or 0
    )
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_pages = ceil(total_items / per_page)

    movies = await get_all_movies(db=db, per_page=per_page, page=page)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page_url = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page_url = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return schemas.MovieListResponseSchema(
        movies=[schemas.MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=prev_page_url,
        next_page=next_page_url,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/", response_model=schemas.MovieDetailSchema, status_code=201
)
async def create_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie: schemas.MovieCreateScheme,
):
    if await get_movie_by_name_and_date(db, movie.name, movie.date):
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )
    try:
        return await create_movie_db(db, movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def retrieve_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int,
):
    movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .execution_options(populate_existing=True)
    )
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return schemas.MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int,
):
    movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int,
    movie: schemas.MovieUpdateScheme,
):
    try:
        found = await patch_movie(db=db, movie_id=movie_id, movie=movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if not found:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return {"detail": "Movie updated successfully."}
