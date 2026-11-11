from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
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


def movie_options():
    return (
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    )


async def get_or_create(db: AsyncSession, model, **filters):
    obj = await db.scalar(select(model).filter_by(**filters))
    if obj is None:
        obj = model(**filters)
        db.add(obj)
        await db.flush()
    return obj


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id))) or 0
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
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
        country = await get_or_create(db, CountryModel, code=movie_data.country)
        genres = [await get_or_create(db, GenreModel, name=n) for n in movie_data.genres]
        actors = [await get_or_create(db, ActorModel, name=n) for n in movie_data.actors]
        languages = [await get_or_create(db, LanguageModel, name=n) for n in movie_data.languages]

        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country_id=country.id,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        db.add(movie)
        await db.commit()
        movie_id = movie.id
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id).options(*movie_options())
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id).options(*movie_options())
    )
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
