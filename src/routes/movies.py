from __future__ import annotations

from math import ceil
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    CountryModel,
    LanguageModel,
)
from database.session_sqlite import get_db
from schemas.movies import (
    MovieBriefSchema,
    MovieFullSchema,
    MoviesListResponse,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


def _path_only(url: str) -> str:
    return urlparse(url).path


async def _get_or_create(
    db: AsyncSession,
    model,
    /,
    *,
    by: dict,
    defaults: dict | None = None,
):
    res = await db.execute(select(model).filter_by(**by))
    obj = res.scalar_one_or_none()
    if obj:
        return obj
    obj = model(**by, **(defaults or {}))
    db.add(obj)
    await db.flush()
    return obj


def _serialize_full(m: MovieModel) -> MovieFullSchema:
    return MovieFullSchema(
        id=m.id,
        name=m.name,
        date=m.date,
        score=m.score,
        overview=m.overview,
        status=m.status,
        budget=float(m.budget) if m.budget is not None else None,
        revenue=float(m.revenue) if m.revenue is not None else None,
        country=None
        if m.country is None
        else {"id": m.country.id, "code": m.country.code, "name": m.country.name},
        genres=[{"id": g.id, "name": g.name} for g in (m.genres or [])],
        actors=[{"id": a.id, "name": a.name} for a in (m.actors or [])],
        languages=[{"id": lang.id, "name": lang.name} for lang in (m.languages or [])],
    )


@router.get("/", response_model=MoviesListResponse)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = (
        await db.execute(select(func.count()).select_from(MovieModel))
    ).scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = [
        MovieBriefSchema(
            id=m.id,
            name=m.name,
            date=m.date,
            score=m.score,
            overview=m.overview,
        )
        for m in rows
    ]

    # Тести очікують шляхи БЕЗ /api/v1
    base_path = "/theater/movies/"
    prev_page: Optional[str] = (
        f"{base_path}?page={page-1}&per_page={per_page}" if page > 1 else None
    )
    next_page: Optional[str] = (
        f"{base_path}?page={page+1}&per_page={per_page}" if page < total_pages else None
    )

    return MoviesListResponse(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/", response_model=MovieFullSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    payload: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    # Дублікат
    dup = await db.execute(
        select(MovieModel).where(
            and_(MovieModel.name == payload.name, MovieModel.date == payload.date)
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{payload.name}' and release date "
                f"'{payload.date}' already exists."
            ),
        )

    # country обов’язкова (NOT NULL у моделі)
    if not payload.country:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    # Підготуємо звʼязані сутності
    country = await _get_or_create(db, CountryModel, by={"code": payload.country})

    # Створюємо фільм з country
    movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country=country,
    )
    db.add(movie)

    # ВАЖЛИВО: отримати id і попередньо завантажити колекції, щоб не було lazy-load у сеттері
    await db.flush()
    await db.refresh(movie, attribute_names=["genres", "actors", "languages"])

    # M2M
    if payload.genres:
        movie.genres = [await _get_or_create(db, GenreModel, by={"name": g}) for g in payload.genres]
    if payload.actors:
        movie.actors = [await _get_or_create(db, ActorModel, by={"name": a}) for a in payload.actors]
    if payload.languages:
        movie.languages = [
            await _get_or_create(db, LanguageModel, by={"name": lang_name})
            for lang_name in payload.languages
        ]

    await db.commit()

    # Перечитуємо з eager-load і .unique()
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    movie = (await db.execute(stmt)).unique().scalar_one()
    return _serialize_full(movie)


@router.get("/{movie_id}/", response_model=MovieFullSchema)
async def movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    # Eager-load + .unique()
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
    res = await db.execute(stmt)
    movie = res.unique().scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return _serialize_full(movie)


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = res.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = res.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    try:
        if payload.name is not None:
            movie.name = payload.name
        if payload.date is not None:
            movie.date = payload.date
        if payload.score is not None:
            movie.score = payload.score
        if payload.overview is not None:
            movie.overview = payload.overview
        if payload.status is not None:
            movie.status = payload.status
        if payload.budget is not None:
            movie.budget = payload.budget
        if payload.revenue is not None:
            movie.revenue = payload.revenue
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    await db.commit()
    return {"detail": "Movie updated successfully."}
