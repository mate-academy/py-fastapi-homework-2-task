import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()

NOT_FOUND = "Movie with the given ID was not found."
INVALID_DATA = "Invalid input data."
LINKS_BASE = "/theater/movies/"


async def get_or_create(
        db: AsyncSession,
        model: type,
        field: str,
        value: str,
):
    column = getattr(model, field)
    instance = await db.scalar(select(model).where(column == value))
    if instance is None:
        instance = model(**{field: value})
        db.add(instance)
        await db.flush()
    return instance


async def get_or_create_many(
        db: AsyncSession,
        model: type,
        field: str,
        values: list[str],
) -> list:
    unique_values = list(dict.fromkeys(values))
    return [
        await get_or_create(db, model, field, value)
        for value in unique_values
    ]


async def load_movie(db: AsyncSession, movie_id: int) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.scalar_one_or_none()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
) -> dict:
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    prev_page = (
        f"{LINKS_BASE}?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"{LINKS_BASE}?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )

    return {
        "movies": result.scalars().all(),
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieModel:
    movie = await load_movie(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
        data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieModel:
    duplicate = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == data.name,
            MovieModel.date == data.date,
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{data.name}' and release date "
                f"'{data.date}' already exists."
            ),
        )

    try:
        country = await get_or_create(db, CountryModel, "code", data.country)
        movie = MovieModel(
            name=data.name,
            date=data.date,
            score=data.score,
            overview=data.overview,
            status=data.status,
            budget=data.budget,
            revenue=data.revenue,
            country=country,
            genres=await get_or_create_many(
                db, GenreModel, "name", data.genres
            ),
            actors=await get_or_create_many(
                db, ActorModel, "name", data.actors
            ),
            languages=await get_or_create_many(
                db, LanguageModel, "name", data.languages
            ),
        )
        db.add(movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail=INVALID_DATA)

    return await load_movie(db, movie.id)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> Response:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    await db.delete(movie)
    await db.commit()
    return Response(status_code=204)


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
) -> dict:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail=INVALID_DATA)

    return {"detail": "Movie updated successfully."}
