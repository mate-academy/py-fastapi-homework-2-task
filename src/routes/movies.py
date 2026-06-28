from typing import Annotated, TypeVar

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]
Page = Annotated[int, Query(ge=1)]
PerPage = Annotated[int, Query(ge=1, le=20)]
ModelType = TypeVar("ModelType", CountryModel, GenreModel, ActorModel, LanguageModel)

NOT_FOUND_MESSAGE = "Movie with the given ID was not found."


async def get_movie_with_details(db: AsyncSession, movie_id: int) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.unique().scalars().first()


async def get_or_create_by_field(
    db: AsyncSession,
    model: type[ModelType],
    field_name: str,
    value: str,
) -> ModelType:
    field = getattr(model, field_name)
    result = await db.execute(select(model).where(field == value))
    item = result.scalars().first()

    if item is not None:
        return item

    item = model(**{field_name: value})
    db.add(item)
    await db.flush()
    return item


async def get_or_create_items(
    db: AsyncSession,
    model: type[ModelType],
    names: list[str],
) -> list[ModelType]:
    items = []
    for name in names:
        item = await get_or_create_by_field(db, model, "name", name)
        items.append(item)
    return items


def bad_request() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid input data.",
    )


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: DbSession,
    page: Page = 1,
    per_page: PerPage = 10,
) -> MovieListResponseSchema:
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_items = total_items or 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = list(result.scalars().all())

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = (total_items + per_page - 1) // per_page
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
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    db: DbSession,
    payload: dict = Body(...),
) -> MovieModel:
    try:
        movie_data = MovieCreateSchema.model_validate(payload)
    except ValidationError:
        raise bad_request()

    duplicate = await db.scalar(
        select(MovieModel.id).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    try:
        country = await get_or_create_by_field(db, CountryModel, "code", movie_data.country)
        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country,
            genres=await get_or_create_items(db, GenreModel, movie_data.genres),
            actors=await get_or_create_items(db, ActorModel, movie_data.actors),
            languages=await get_or_create_items(db, LanguageModel, movie_data.languages),
        )
        db.add(movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise bad_request()

    created_movie = await get_movie_with_details(db, movie.id)
    return created_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: DbSession) -> MovieModel:
    movie = await get_movie_with_details(db, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_MESSAGE,
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: DbSession) -> None:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_MESSAGE,
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    db: DbSession,
    payload: dict = Body(...),
) -> dict[str, str]:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND_MESSAGE,
        )

    try:
        movie_data = MovieUpdateSchema.model_validate(payload)
    except ValidationError:
        raise bad_request()

    update_data = movie_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise bad_request()

    return {"detail": "Movie updated successfully."}
