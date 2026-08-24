import math
from sqlalchemy.exc import IntegrityError
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from utility.utility import (
    create_country,
    create_actors,
    create_genres,
    create_languages,
)

from database import MovieModel, get_db
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)
from sqlalchemy.orm import selectinload

router = APIRouter()

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: DatabaseSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
) -> MovieListResponseSchema:
    total_items = int(await db.scalar(select(func.count()).select_from(MovieModel)))
    total_pages = math.ceil(total_items / per_page) if total_items else 0

    if page > total_pages or total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

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


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(db: DatabaseSession, movie_id: int) -> MovieDetailSchema:
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return MovieDetailSchema.model_validate(movie)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    db: DatabaseSession, movie: MovieCreateSchema
) -> MovieDetailSchema:
    movie_to_check = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )
    if movie_to_check.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )
    try:
        country = await create_country(db, movie.country)
        genres = await create_genres(db, movie.genres)
        languages = await create_languages(db, movie.languages)
        actors = await create_actors(db, movie.actors)
        movie_to_create = MovieModel(
            **movie.model_dump(exclude={"country", "actors", "genres", "languages"}),
            country=country,
            genres=genres,
            languages=languages,
            actors=actors,
        )
        db.add(movie_to_create)
        await db.commit()
        query = (
            select(MovieModel)
            .where(MovieModel.id == movie_to_create.id)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.languages),
            )
        )
        result = await db.execute(query)
        return MovieDetailSchema.model_validate(result.scalar_one_or_none())
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(db: DatabaseSession, movie_id: int) -> None:
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    try:
        await db.delete(movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error with deletion")


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
    db: DatabaseSession, movie: MovieUpdateSchema, movie_id: int
) -> dict:
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result_movie = (await db.execute(query)).scalar_one_or_none()
    if not result_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    try:
        query = (
            update(MovieModel)
            .where(MovieModel.id == movie_id)
            .values(**movie.model_dump(exclude_none=True))
        )
        await db.execute(query)
        await db.commit()
        return {"detail": "Movie updated successfully."}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
