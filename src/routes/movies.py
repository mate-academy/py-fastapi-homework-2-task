from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MessageResponseSchema,
    MovieCreateSchema,
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()

RelatedModel = TypeVar("RelatedModel", GenreModel, ActorModel, LanguageModel)


def movie_detail_options() -> tuple:
    return (
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
    )


async def get_movie_with_relations(db: AsyncSession, movie_id: int) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(*movie_detail_options())
        .where(MovieModel.id == movie_id)
    )
    return result.unique().scalars().first()


async def get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    country = await db.scalar(select(CountryModel).where(CountryModel.code == code))
    if country is not None:
        return country

    country = CountryModel(code=code, name=None)
    db.add(country)
    await db.flush()
    return country


async def get_or_create_related(
    db: AsyncSession,
    model: type[RelatedModel],
    names: list[str],
) -> list[RelatedModel]:
    items = []
    for name in names:
        item = await db.scalar(select(model).where(model.name == name))
        if item is None:
            item = model(name=name)
            db.add(item)
            await db.flush()
        items.append(item)
    return items


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
) -> dict:
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if not total_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_payload: dict[str, object],
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    try:
        movie_data = MovieCreateSchema.model_validate(movie_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.") from exc

    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if existing_movie is not None:
        detail = (
            f"A movie with the name '{movie_data.name}' and release date "
            f"'{movie_data.date}' already exists."
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    country = await get_or_create_country(db=db, code=movie_data.country)
    genres = await get_or_create_related(db=db, model=GenreModel, names=movie_data.genres)
    actors = await get_or_create_related(db=db, model=ActorModel, names=movie_data.actors)
    languages = await get_or_create_related(db=db, model=LanguageModel, names=movie_data.languages)

    movie = MovieModel(
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

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.") from exc

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def read_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    movie = await get_movie_with_relations(db=db, movie_id=movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", response_model=MessageResponseSchema)
async def update_movie(
    movie_id: int,
    movie_payload: dict[str, object],
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        movie_data = MovieUpdateSchema.model_validate(movie_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.") from exc

    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.") from exc

    return {"detail": "Movie updated successfully."}
