import http
import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateRequest,
    MovieDetailSchema,
    MovieUpdateResponse,
    MovieUpdateRequest,
)

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]


# Write your code here
@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    offset = (page - 1) * per_page
    query = (
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)
    total_items = count_result.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
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
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def add_movie(movie_data: MovieCreateRequest, db: DbSession):
    query = select(MovieModel).filter_by(name=movie_data.name, date=movie_data.date)
    result = await db.execute(query)
    query_movie = result.scalar_one_or_none()
    if query_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}'"
            f" and release date '{movie_data.date}' already exists.",
        )

    country_stmt = select(CountryModel).filter_by(code=movie_data.country)
    country_result = await db.execute(country_stmt)
    country_obj = country_result.scalar_one_or_none()

    if not country_obj:
        country_obj = CountryModel(code=movie_data.country, name=None)
        db.add(country_obj)
        await db.flush()

    db_actors = await get_or_create_objects(db, ActorModel, movie_data.actors)

    db_languages = await get_or_create_objects(db, LanguageModel, movie_data.languages)

    db_genres = await get_or_create_objects(db, GenreModel, movie_data.genres)
    movie_fields = movie_data.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )

    # Распаковываем их через **, а связи передаем явно!
    new_movie = MovieModel(
        **movie_fields,
        country=country_obj,
        genres=db_genres,
        actors=db_actors,
        languages=db_languages,
    )
    db.add(new_movie)
    await db.commit()
    query = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    result = await db.execute(query)
    fresh_movie = result.scalar_one()
    return fresh_movie


async def get_or_create_objects(db, model, values, field="name"):
    objects = []

    for value in values:
        stmt = select(model).filter_by(**{field: value})
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()

        if obj is None:
            obj = model(**{field: value})
            db.add(obj)

        objects.append(obj)

    return objects


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_detail_movie(movie_id: int, db: DbSession):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    movie = await db.execute(query)
    movie = movie.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: DbSession):
    query = select(MovieModel).where(MovieModel.id == movie_id)

    movie = await db.execute(query)
    movie = movie.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", response_model=MovieUpdateResponse)
async def update_movie(movie_id: int, movie_data: MovieUpdateRequest, db: DbSession):
    query = select(MovieModel).where(MovieModel.id == movie_id)

    result = await db.execute(query)
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
