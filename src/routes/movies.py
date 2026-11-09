import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_all_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = math.ceil(total_items / per_page)

    if not total_items or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    base = "/theater/movies/"
    return {
        "movies": movies,
        "prev_page": f"{base}?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "next_page": f"{base}?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def _get_or_create_by_name(db: AsyncSession, model, names: list[str]) -> list:
    items = []
    for name in dict.fromkeys(names):
        obj = await db.scalar(select(model).where(model.name == name))
        if not obj:
            obj = model(name=name)
            db.add(obj)
        items.append(obj)
    return items


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = await db.scalar(select(CountryModel).where(CountryModel.code == movie.country))
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)

    new_movie = MovieModel(
        **movie.model_dump(exclude={"country", "genres", "actors", "languages"}),
        country=country,
        genres=await _get_or_create_by_name(db, GenreModel, movie.genres),
        actors=await _get_or_create_by_name(db, ActorModel, movie.actors),
        languages=await _get_or_create_by_name(db, LanguageModel, movie.languages),
    )
    db.add(new_movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    return result.scalars().one()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    db_movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(db_movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    db_movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    for field, value in movie.model_dump(exclude_unset=True).items():
        setattr(db_movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
