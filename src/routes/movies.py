from typing import Annotated

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.schemas.movies import (
    MessageResponseSchema, MovieCreateRequestSchema, MovieDetailResponseSchema,
    MovieListResponseSchema, MovieUpdateRequestSchema,
)

router = APIRouter()


async def _get_movie(
        db: AsyncSession,
        movie_id: int,
) -> MovieModel:
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            joinedload(MovieModel.country)
        )
    )

    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return movie


async def get_or_create_many(
        session: AsyncSession,
        model: type,
        names: list[str]
) -> list:
    result_objects = []

    for name in names:
        query = select(model).where(model.name == name)
        existing_obj = await session.scalar(query)

        if existing_obj:
            result_objects.append(existing_obj)
        else:
            new_obj = model(name=name)
            session.add(new_obj)
            result_objects.append(new_obj)

    return result_objects


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK
)
async def get_movies(
        db: Annotated[AsyncSession, Depends(get_db)],
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        per_page: Annotated[
            int, Query(ge=1, le=20, description="Items per page")] = 10
):
    offset = (page - 1) * per_page
    count_query = select(func.count()).select_from(MovieModel)
    total_items = await db.scalar(count_query)

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    query = select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/theater/movies/"
    prev_page_url = None
    if page > 1:
        prev_page_url = f"{base_url}?page={page - 1}&per_page={per_page}"

    next_page_url = None
    if page < total_pages:
        next_page_url = f"{base_url}?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page_url,
        "next_page": next_page_url,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        body: MovieCreateRequestSchema
) -> MovieModel:
    duplicate_query = select(MovieModel).where(
        MovieModel.name == body.name,
        MovieModel.date == body.date
    )

    existing_movie = await db.scalar(duplicate_query)

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{body.name}' and release date '{body.date}' already exists."
        )

    genres_objects = await get_or_create_many(db, GenreModel, body.genres)
    actors_objects = await get_or_create_many(db, ActorModel, body.actors)
    languages_objects = await get_or_create_many(db, LanguageModel,
                                                 body.languages)
    country_query = select(CountryModel).where(
        CountryModel.code == body.country)
    country_obj = await db.scalar(country_query)
    if not country_obj:
        country_obj = CountryModel(code=body.country)
        db.add(country_obj)
    new_movie = MovieModel(
        name=body.name,
        date=body.date,
        score=body.score,
        overview=body.overview,
        status=body.status,
        budget=body.budget,
        revenue=body.revenue,
        country=country_obj,
        genres=genres_objects,
        actors=actors_objects,
        languages=languages_objects
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return new_movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_200_OK
)
async def get_movie_by_id(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)]
) -> MovieModel:
    return await _get_movie(db, movie_id)


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK
)
async def update_movie(
        movie_id: int,
        body: MovieUpdateRequestSchema,
        db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        return {"detail": "Movie updated successfully."}

    for key, value in update_data.items():
        if key == 'id':
            continue
        setattr(movie, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
