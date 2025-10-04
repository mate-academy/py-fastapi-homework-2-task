from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import (
    MovieModel,
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieUpdateSchema,
    PaginatedMovieListSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


async def _get_or_create_country(session: AsyncSession, code: str) -> CountryModel:
    normalized_code = (code or "").strip().upper()
    if not (normalized_code.isalpha() and len(normalized_code) in (2, 3)):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    res = await session.execute(
        select(CountryModel).where(CountryModel.code == normalized_code)
    )
    country = res.scalars().first()
    if country:
        return country

    country = CountryModel(code=normalized_code)
    session.add(country)
    await session.flush()
    return country


async def _get_or_create_named_entities(
    session: AsyncSession, model, names: Iterable[str]
) -> list:
    instances: list = []
    created = False

    for name in dict.fromkeys(names or []):
        clean = (name or "").strip()
        if not clean:
            continue

        res = await session.execute(select(model).where(model.name == clean))
        obj = res.scalars().first()
        if obj is None:
            obj = model(name=clean)
            session.add(obj)
            created = True
        instances.append(obj)

    if created:
        await session.flush()

    return instances


def _page_link(base_path: str, page: int, per_page: int) -> str:
    return f"{base_path}?page={page}&per_page={per_page}"


@router.get("/", response_model=PaginatedMovieListSchema)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> PaginatedMovieListSchema:
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    q = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    res = await db.execute(q)
    movies = res.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_path = "/theater/movies/"

    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    if page > 1:
        prev_page = _page_link(base_path, page - 1, per_page)
    if page < total_pages:
        next_page = _page_link(base_path, page + 1, per_page)

    return PaginatedMovieListSchema(
        movies=movies,
        total_pages=total_pages,
        total_items=total_items,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_in: MovieCreateSchema, db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    if movie_in.date > (date.today() + timedelta(days=365)):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if len(movie_in.name) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if not (0 <= movie_in.score <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie_in.budget < 0 or movie_in.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    dup = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_in.name, MovieModel.date == movie_in.date
        )
    )
    if dup:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_in.name}' and release date "
                f"'{movie_in.date.isoformat()}' already exists."
            ),
        )

    country = await _get_or_create_country(db, movie_in.country)
    genres = await _get_or_create_named_entities(db, GenreModel, movie_in.genres)
    actors = await _get_or_create_named_entities(db, ActorModel, movie_in.actors)
    languages = await _get_or_create_named_entities(db, LanguageModel, movie_in.languages)

    movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_in.name}' and release date "
                f"'{movie_in.date.isoformat()}' already exists."
            ),
        ) from exc

    res = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    full = res.scalars().first()
    return full


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    res = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    movie = res.scalars().first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    res = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = res.scalars().first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int, movie_in: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = res.scalars().first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    data = movie_in.model_dump(exclude_unset=True) \
        if hasattr(movie_in, "model_dump")\
        else movie_in.dict(exclude_unset=True)

    allowed = {"name", "date", "score", "overview", "status", "budget", "revenue"}
    data = {k: v for k, v in data.items() if k in allowed}

    if "date" in data and data["date"] is not None:
        if data["date"] > (date.today() + timedelta(days=365)):
            raise HTTPException(status_code=400, detail="Invalid input data.")
    if "name" in data and data["name"] is not None and len(data["name"]) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "score" in data and data["score"] is not None and not (0 <= data["score"] <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "budget" in data and data["budget"] is not None and data["budget"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if "revenue" in data and data["revenue"] is not None and data["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for field, value in data.items():
        if value is not None:
            setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
