from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from httpx import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import models
from database import MovieModel, get_db
from schemas import (
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieCreateResponseSchema,
    MovieUpdateResponseSchema,
)

router = APIRouter()


def build_page_link(page: int, per_page: int, total_pages: int) -> Optional[str]:
    if page < 1 or page > total_pages:
        return None
    return f"/theater/movies/?page={page}&per_page={per_page}"


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_items = total_items or 0

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = ceil(total_items / per_page)
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id)
        .limit(per_page)
        .offset(offset)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=build_page_link(page - 1, per_page, total_pages),
        next_page=build_page_link(page + 1, per_page, total_pages),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_data: MovieCreateResponseSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = models.MovieModel(**movie_data.model_dump())

    db.add(movie)
    db.commit()
    db.refresh(movie)

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_Deleted)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    db.delete(MovieModel, movie_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateResponseSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    db.commit()
    db.refresh(movie)

    return movie
