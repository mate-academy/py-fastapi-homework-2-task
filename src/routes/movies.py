import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateRequest,
    MovieUpdateRequest,
)

router = APIRouter(prefix="/movies", tags=["movies"])


async def get_or_create_entities(
    db: AsyncSession, model, names: list, field_name="name"
):
    if not names:
        return []

    stmt = select(model).where(getattr(model, field_name).in_(names))
    result = await db.execute(stmt)
    existing_entities = list(result.scalars().all())
    existing_names = {getattr(e, field_name) for e in existing_entities}

    new_entities = []
    for name in names:
        if name not in existing_names:
            new_obj = model(**{field_name: name})
            db.add(new_obj)
            new_entities.append(new_obj)

    if new_entities:
        await db.flush()

    return existing_entities + new_entities


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    offset = (page - 1) * per_page
    if offset >= total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = (
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    )
    movie_result = await db.execute(stmt)
    movies = movie_result.unique().scalars().all()

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
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


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(payload: MovieCreateRequest, db: AsyncSession = Depends(get_db)):
    dup_stmt = select(MovieModel).where(
        MovieModel.name == payload.name, MovieModel.date == payload.date
    )
    dup_result = await db.execute(dup_stmt)
    if dup_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.",
        )

    country_stmt = select(CountryModel).where(CountryModel.code == payload.country)
    country_result = await db.execute(country_stmt)
    country_obj = country_result.scalar_one_or_none()

    if not country_obj:
        country_obj = CountryModel(code=payload.country, name=None)
        db.add(country_obj)
        await db.flush()

    genres_objs = await get_or_create_entities(db, GenreModel, payload.genres)
    actors_objs = await get_or_create_entities(db, ActorModel, payload.actors)
    languages_objs = await get_or_create_entities(db, LanguageModel, payload.languages)

    new_movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country=country_obj,
        genres=genres_objs,
        actors=actors_objs,
        languages=languages_objs,
    )

    db.add(new_movie)
    await db.commit()
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    movie_response = result.unique().scalar_one()

    return movie_response


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int, payload: MovieUpdateRequest, db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
