from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieStatusEnum,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieDetailSchema,
    MovieUpdate,
)

router = APIRouter()


async def get_or_create(db: AsyncSession, model, **lookup):
    obj = (await db.execute(select(model).filter_by(**lookup))).scalars().first()
    if obj is None:
        obj = model(**lookup)
        db.add(obj)
        await db.flush()
    return obj


def movie_query():
    return select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
    )


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count(MovieModel.id)))
    if total == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total + per_page - 1) // per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = result.scalars().all()

    if not items:
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
        "movies": items,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total,
    }


@router.post(
    "/movies/",
    response_model=MovieCreateResponseSchema,
    status_code=201,
)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    existing = (
        await db.execute(
            select(MovieModel).where(
                MovieModel.name == movie_data.name,
                MovieModel.date == movie_data.date,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    country = await get_or_create(db, CountryModel, code=movie_data.country)
    genres = [await get_or_create(db, GenreModel, name=n) for n in movie_data.genres]
    actors = [await get_or_create(db, ActorModel, name=n) for n in movie_data.actors]
    languages = [
        await get_or_create(db, LanguageModel, name=n) for n in movie_data.languages
    ]

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=MovieStatusEnum(movie_data.status),
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(movie_query().where(MovieModel.id == movie_id))
    movie = result.unique().scalars().first()
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    updates = movie_data.model_dump(exclude_unset=True)
    if "status" in updates:
        updates["status"] = MovieStatusEnum(updates["status"])
    for field, value in updates.items():
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
