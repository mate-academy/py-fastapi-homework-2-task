import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateRequestSchema,
    MovieUpdateRequestSchema,
)

router = APIRouter()


async def _get_or_create(db: AsyncSession, model, unique_field: str, value: str):
    stmt = select(model).where(getattr(model, unique_field) == value)
    result = await db.execute(stmt)
    instance = result.scalars().first()
    if instance is None:
        instance = model(**{unique_field: value})
        db.add(instance)
        await db.flush()
    return instance


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie_data: MovieCreateRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date,
    )
    result = await db.execute(stmt)
    existing_movie = result.scalars().first()
    if existing_movie is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    country = await _get_or_create(db, CountryModel, "code", movie_data.country)
    genres = [await _get_or_create(db, GenreModel, "name", name) for name in movie_data.genres]
    actors = [await _get_or_create(db, ActorModel, "name", name) for name in movie_data.actors]
    languages = [await _get_or_create(db, LanguageModel, "name", name) for name in movie_data.languages]

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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateRequestSchema,
        db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_fields = movie_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
