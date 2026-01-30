from __future__ import annotations

import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.session_postgresql import get_postgresql_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieReadSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


def _page_link(request: Request, page: int, per_page: int) -> str:
    root_path = request.scope.get("root_path", "") or ""
    path = request.url.path
    if root_path and not path.startswith(root_path):
        path = f"{root_path}{path}"
    return f"{path}?page={page}&per_page={per_page}"


def _validate_release_date_not_too_future(d: date) -> None:
    if d > (date.today() + timedelta(days=365)):
        raise HTTPException(status_code=400, detail="Invalid input data.")


async def _get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    code = code.strip().upper()
    res = await db.execute(select(CountryModel).where(CountryModel.code == code))
    country = res.scalar_one_or_none()
    if country is not None:
        return country

    country = CountryModel(code=code)
    db.add(country)
    await db.flush()
    return country


async def _get_or_create_by_name(
    db: AsyncSession,
    model_cls,
    name: str,
):
    name = name.strip()
    if not name:
        return None

    res = await db.execute(select(model_cls).where(model_cls.name == name))
    obj = res.scalar_one_or_none()
    if obj is not None:
        return obj

    obj = model_cls(name=name)
    db.add(obj)
    await db.flush()
    return obj


async def _load_movie_full(db: AsyncSession, movie_id: int) -> MovieModel | None:
    q = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    res = await db.execute(q)
    return res.scalar_one_or_none()


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_postgresql_db),
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if not total_items or total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
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

    prev_page = _page_link(request, page - 1, per_page) if page > 1 else None
    next_page = _page_link(request, page + 1, per_page) if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": int(total_items),
    }


@router.post("/", response_model=MovieReadSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    payload: MovieCreateSchema,
    db: AsyncSession = Depends(get_postgresql_db),
):
    _validate_release_date_not_too_future(payload.date)

    if len(payload.name) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == payload.name,
            MovieModel.date == payload.date,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.",
        )

    try:
        country = await _get_or_create_country(db, payload.country)

        genres = []
        for g in payload.genres:
            obj = await _get_or_create_by_name(db, GenreModel, g)
            if obj is not None:
                genres.append(obj)

        actors = []
        for a in payload.actors:
            obj = await _get_or_create_by_name(db, ActorModel, a)
            if obj is not None:
                actors.append(obj)

        languages = []
        for l in payload.languages:
            obj = await _get_or_create_by_name(db, LanguageModel, l)
            if obj is not None:
                languages.append(obj)

        movie = MovieModel(
            name=payload.name,
            date=payload.date,
            score=payload.score,
            overview=payload.overview,
            status=payload.status,
            budget=payload.budget,
            revenue=payload.revenue,
            country_id=country.id,
        )

        movie.country = country
        movie.genres = genres
        movie.actors = actors
        movie.languages = languages

        db.add(movie)
        await db.flush()
        await db.commit()

        created = await _load_movie_full(db, movie.id)
        return created

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/{movie_id}/", response_model=MovieReadSchema)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_postgresql_db),
):
    movie = await _load_movie_full(db, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_postgresql_db),
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    db: AsyncSession = Depends(get_postgresql_db),
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    if payload.date is not None:
        _validate_release_date_not_too_future(payload.date)

    if payload.name is not None and len(payload.name) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    try:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(movie, field, value)

        await db.commit()
        return {"detail": "Movie updated successfully."}

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
