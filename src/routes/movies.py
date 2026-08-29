from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import Response
from starlette import status

from database import models
from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas import (
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieCreateResponseSchema,
    MovieUpdateResponseSchema,
    MovieUpdateSuccessResponseSchema,
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
        .order_by(MovieModel.id.desc())
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
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

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
    duplicate_result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if duplicate_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date.isoformat()}' already exists."
            ),
        )

    country = await get_or_create_related_entity(
        db,
        CountryModel,
        "code",
        movie_data.country,
    )
    genres = await get_or_create_related_entities(
        db,
        GenreModel,
        "name",
        movie_data.genres,
    )
    actors = await get_or_create_related_entities(
        db,
        ActorModel,
        "name",
        movie_data.actors,
    )
    languages = await get_or_create_related_entities(
        db,
        LanguageModel,
        "name",
        movie_data.languages,
    )

    movie = models.MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    movie = result.scalars().first()

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
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
    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/", response_model=MovieUpdateSuccessResponseSchema)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateResponseSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_data.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()

    return MovieUpdateSuccessResponseSchema(detail="Movie updated successfully.")


async def get_or_create_related_entity(
    db: AsyncSession,
    model: type[CountryModel | GenreModel | ActorModel | LanguageModel],
    field_name: str,
    value: str,
):
    result = await db.execute(
        select(model).where(getattr(model, field_name) == value)
    )
    entity = result.scalars().first()

    if entity is None:
        entity = model(**{field_name: value})
        db.add(entity)
        await db.flush()

    return entity


async def get_or_create_related_entities(
    db: AsyncSession,
    model: type[GenreModel | ActorModel | LanguageModel],
    field_name: str,
    values: list[str],
):
    entities = []
    for value in values:
        entity = await get_or_create_related_entity(db, model, field_name, value)
        entities.append(entity)
    return entities
