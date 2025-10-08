from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud import create_movie, delete_movie, update_movie, get_movie
from database import get_db, MovieModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListSchema,
    MovieUpdateSchema,
    MovieSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListSchema)
async def list_movies(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
    db: AsyncSession = Depends(get_db),
):
    count = select(func.count(MovieModel.id))
    count_result = await db.execute(count)
    total_items = count_result.unique().scalar_one_or_none()
    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.unique().scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}"

    return MovieListSchema(
        movies=[MovieSchema.model_validate(m) for m in movies],
        total_items=total_items,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    if existing_movie.unique().scalars().all():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name"
            f" '{movie.name}' and "
            f"release"
            f" date '{movie.date}'"
            f" already exists.",
        )

    new_movie = await create_movie(db, movie)
    await db.refresh(new_movie)
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    movie_result = result.scalars().unique().one()
    return MovieDetailSchema.model_validate(movie_result)


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    movie_schema = MovieDetailSchema.model_validate(movie)
    return movie_schema.model_dump()


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def movie_destroy(movie_id: int, db: AsyncSession = Depends(get_db)):
    await delete_movie(db, movie_id)


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def movie_patch(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    await update_movie(db, movie, movie_id)
    return {"detail": "Movie updated successfully."}
