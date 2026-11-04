import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)


router = APIRouter()

MOVIE_NOT_FOUND = "Movie with the given ID was not found."
INVALID_INPUT = "Invalid input data."


async def get_movie_with_relations(db: AsyncSession, movie_id: int):
    """Load a movie together with country, genres, actors and languages."""
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
    return result.unique().scalar_one_or_none()


async def get_or_create_by_name(db: AsyncSession, model, names: list[str]):
    """Find entities by name, creating the ones that do not exist yet."""
    items = []
    for name in dict.fromkeys(names):  # removes duplicates, keeps order
        item = await db.scalar(select(model).where(model.name == name))
        if item is None:
            item = model(name=name)
            db.add(item)
            await db.flush()
        items.append(item)
    return items


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(*MovieModel.default_order_by())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    try:
        country = await db.scalar(
            select(CountryModel).where(CountryModel.code == movie_data.country)
        )
        if country is None:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()

        genres = await get_or_create_by_name(db, GenreModel, movie_data.genres)
        actors = await get_or_create_by_name(db, ActorModel, movie_data.actors)
        languages = await get_or_create_by_name(db, LanguageModel, movie_data.languages)

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
        raise HTTPException(status_code=400, detail=INVALID_INPUT)

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_with_relations(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND)
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_with_relations(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND)

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND)

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail=INVALID_INPUT)

    return {"detail": "Movie updated successfully."}
