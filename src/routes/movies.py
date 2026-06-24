from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MessageResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


router = APIRouter()


async def _get_movie_or_404(db: AsyncSession, movie_id: int) -> MovieModel:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.unique().scalars().first()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


async def _get_or_create_by_field(
    db: AsyncSession,
    model,
    field_name: str,
    value: str,
):
    field = getattr(model, field_name)
    result = await db.execute(select(model).where(field == value))
    instance = result.scalars().first()
    if instance is not None:
        return instance

    instance = model(**{field_name: value})
    db.add(instance)
    await db.flush()
    return instance


async def _get_or_create_many_by_name(
    db: AsyncSession,
    model,
    names: list[str],
):
    instances = []
    seen_names = set()

    for name in names:
        clean_name = name.strip()
        if not clean_name or clean_name in seen_names:
            continue

        seen_names.add(clean_name)
        instance = await _get_or_create_by_field(db, model, "name", clean_name)
        instances.append(instance)

    return instances


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_payload: dict = Body(),
    db: AsyncSession = Depends(get_db),
):
    try:
        movie_data = MovieCreateSchema.model_validate(movie_payload)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    duplicate_stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date,
    )
    duplicate_result = await db.execute(duplicate_stmt)
    if duplicate_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    try:
        country_code = movie_data.country.strip()
        country = await _get_or_create_by_field(db, CountryModel, "code", country_code)
        genres = await _get_or_create_many_by_name(db, GenreModel, movie_data.genres)
        actors = await _get_or_create_many_by_name(db, ActorModel, movie_data.actors)
        languages = await _get_or_create_many_by_name(db, LanguageModel, movie_data.languages)

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
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    return await _get_movie_or_404(db, movie.id)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await _get_movie_or_404(db, movie_id)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await _get_movie_or_404(db, movie_id)
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/", response_model=MessageResponseSchema)
async def update_movie(
    movie_id: int,
    movie_payload: dict = Body(),
    db: AsyncSession = Depends(get_db),
):
    try:
        movie_data = MovieUpdateSchema.model_validate(movie_payload)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    movie = await _get_movie_or_404(db, movie_id)
    update_data = movie_data.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        setattr(movie, field_name, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    return {"detail": "Movie updated successfully."}
