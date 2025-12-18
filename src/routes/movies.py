from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageSchema,
)

router = APIRouter()

BASE_LIST_URL = "/theater/movies/"


async def _get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    code = code.upper().strip()
    result = await db.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalar_one_or_none()
    if country:
        return country

    country = CountryModel(code=code)
    db.add(country)
    await db.flush()
    return country


async def _get_or_create_named_entities(
    db: AsyncSession,
    model_cls,
    names: list[str],
):
    entities = []
    for raw_name in names or []:
        name = raw_name.strip()
        if not name:
            continue

        result = await db.execute(select(model_cls).where(model_cls.name == name))
        entity = result.scalar_one_or_none()
        if entity is None:
            entity = model_cls(name=name)
            db.add(entity)
            await db.flush()
        entities.append(entity)
    return entities


def _build_page_link(page: int, per_page: int) -> str:
    return f"{BASE_LIST_URL}?page={page}&per_page={per_page}"


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_items = int(total_items or 0)

    total_pages = (total_items + per_page - 1) // per_page if total_items else 0
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = _build_page_link(page - 1, per_page) if page > 1 else None
    next_page = _build_page_link(page + 1, per_page) if page < total_pages else None

    return MovieListResponseSchema(
        movies=[
            MovieListItemSchema(
                id=m.id,
                name=m.name,
                date=m.date,
                score=m.score,
                overview=m.overview,
            )
            for m in movies
        ],
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
    movie_in: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_in.name,
            MovieModel.date == movie_in.date,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_in.name}' and release date "
                f"'{movie_in.date}' already exists."
            ),
        )

    try:
        country = await _get_or_create_country(db, movie_in.country)
        genres = await _get_or_create_named_entities(db, GenreModel, movie_in.genres)
        actors = await _get_or_create_named_entities(db, ActorModel, movie_in.actors)
        languages = await _get_or_create_named_entities(
            db, LanguageModel, movie_in.languages
        )

        movie = MovieModel(
            name=movie_in.name,
            date=movie_in.date,
            score=movie_in.score,
            overview=movie_in.overview,
            status=movie_in.status.value if movie_in.status is not None else None,
            budget=movie_in.budget if movie_in.budget is not None else 0,
            revenue=movie_in.revenue if movie_in.revenue is not None else 0,
            country=country,
        )

        movie.genres = genres
        movie.actors = actors
        movie.languages = languages

        db.add(movie)
        await db.commit()
        await db.refresh(movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    movie = result.unique().scalar_one()

    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=float(movie.budget) if movie.budget is not None else None,
        revenue=float(movie.revenue) if movie.revenue is not None else None,
        country=(
            {
                "id": movie.country.id,
                "code": movie.country.code,
                "name": movie.country.name,
            }
            if movie.country
            else None
        ),
        genres=[{"id": g.id, "name": g.name} for g in (movie.genres or [])],
        actors=[{"id": a.id, "name": a.name} for a in (movie.actors or [])],
        languages=[{"id": lang.id, "name": lang.name} for lang in (movie.languages or [])],
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    movie = result.unique().scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=float(movie.budget) if movie.budget is not None else None,
        revenue=float(movie.revenue) if movie.revenue is not None else None,
        country=(
            {
                "id": movie.country.id,
                "code": movie.country.code,
                "name": movie.country.name,
            }
            if movie.country
            else None
        ),
        genres=[{"id": g.id, "name": g.name} for g in (movie.genres or [])],
        actors=[{"id": a.id, "name": a.name} for a in (movie.actors or [])],
        languages=[{"id": lang.id, "name": lang.name} for lang in (movie.languages or [])],
    )


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()
    return None


@router.patch(
    "/movies/{movie_id}/",
    response_model=MessageSchema,
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    data = movie_in.dict(exclude_unset=True)

    if "status" in data and data["status"] is not None:
        data["status"] = data["status"].value

    try:
        for key, value in data.items():
            setattr(movie, key, value)

        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return MessageSchema(detail="Movie updated successfully.")
