import math
from typing import Annotated

from fastapi import APIRouter, Query, Request, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel, Base
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageResponse
)
from utils import NoMoviesError, MovieAlreadyExistsError

router = APIRouter()


async def get_or_create(db: AsyncSession, model, field: str, value, **kwargs):
    stmt = select(model).filter_by(**{field: value})
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance

    instance = model(**{field: value}, **kwargs)
    db.add(instance)
    await db.flush()
    return instance


async def operate_list(
        db: AsyncSession,
        items_list: list,
        model,
        field: str,
) -> list:
    result_objects = []
    for value in items_list:
        obj = await get_or_create(db, model, field, value)
        result_objects.append(obj)
    return result_objects


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieDetailSchema,
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        )
    )

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' "
                   f"and release date '{movie_data.date}' already exists."
        )

    try:
        country = await get_or_create(
            db=db,
            model=CountryModel,
            field="code",
            value=movie_data.country
        )

        new_movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country
        )

        db.add(new_movie)

        new_movie.genres = await operate_list(
            db, movie_data.genres, GenreModel, "name"
        )
        new_movie.actors = await operate_list(
            db, movie_data.actors, ActorModel, "name"
        )
        new_movie.languages = await operate_list(
            db, movie_data.languages, LanguageModel, "name"
        )

        await db.commit()

        query = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages)
            )
            .where(MovieModel.id == new_movie.id)
        )

        result = await db.execute(query)
        return result.scalar_one()

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieDetailSchema:
    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )

    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    movie = await db.get(MovieModel,
                         movie_id)

    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
)
async def update_movie(
    movie_id: int,
    movie_update: MovieUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    return {"detail": "Movie updated successfully."}
