from math import ceil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response
from sqlalchemy.orm import selectinload

from schemas.movies import (
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
)

from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    CountryModel,
    LanguageModel,
)

from database import get_db

router = APIRouter(prefix="/movies")


def _page_link(base: str, page: int, per_page: int) -> str:
    return f"{base}?page={page}&per_page={per_page}"


@router.get("/", response_model=MovieListResponseSchema, status_code=status.HTTP_200_OK)
async def list_movies(
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    base_path = "/theater/movies/"

    total_items = await session.scalar(select(func.count()).select_from(MovieModel))
    if total_items == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = max(1, ceil(total_items / per_page))
    if page > total_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    offset = (page - 1) * per_page

    rows = await session.execute(
        select(
            MovieModel.id,
            MovieModel.name,
            MovieModel.date,
            MovieModel.score,
            MovieModel.overview,
        )
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    items = rows.all()
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    movies = [
        MovieListItemSchema(
            id=r[0],
            name=r[1],
            date=r[2],
            score=float(r[3]) if r[3] is not None else 0.0,
            overview=r[4],
        )
        for r in items
    ]

    prev_page = None if page <= 1 else _page_link(base_path, page - 1, per_page)
    next_page = None if page >= total_pages else _page_link(base_path, page + 1, per_page)

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def _get_or_create_country(session: AsyncSession, code: Optional[str]) -> Optional[CountryModel]:
    if not code:
        return None
    code = code.strip().upper()

    country = await session.scalar(select(CountryModel).where(CountryModel.code == code))
    if country:
        return country

    country = CountryModel(code=code, name=None)
    session.add(country)
    await session.flush()
    return country


async def _get_or_create_by_names(session: AsyncSession, model, names: List[str]) -> List:
    if not names:
        return []
    normalized = [n.strip() for n in names if n and n.strip()]
    if not normalized:
        return []

    existing = (
        await session.execute(select(model).where(model.name.in_(normalized)))
    ).scalars().all()

    existing_names = {e.name for e in existing}
    to_create = [model(name=n) for n in normalized if n not in existing_names]
    for obj in to_create:
        session.add(obj)
    if to_create:
        await session.flush()
    return existing + to_create


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(payload: MovieCreateSchema, session: AsyncSession = Depends(get_db)):
    duplicate = await session.scalar(
        select(func.count())
        .select_from(MovieModel)
        .where(and_(MovieModel.name == payload.name, MovieModel.date == payload.date))
    )
    if duplicate and duplicate > 0:
        msg = f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)

    country = await _get_or_create_country(session, payload.country)
    genres = await _get_or_create_by_names(session, GenreModel, payload.genres)
    actors = await _get_or_create_by_names(session, ActorModel, payload.actors)
    languages = await _get_or_create_by_names(session, LanguageModel, payload.languages)

    movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
    )

    session.add(movie)

    movie.country = country
    movie.genres = genres or []
    movie.actors = actors or []
    movie.languages = languages or []

    await session.commit()

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    movie_db = await session.scalar(stmt)
    return MovieDetailSchema.model_validate(movie_db, from_attributes=True)


@router.get("/{movie_id}/", response_model=MovieDetailSchema, status_code=status.HTTP_200_OK)
async def get_movie_details(movie_id: int, session: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = await session.scalar(stmt)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return MovieDetailSchema.model_validate(movie, from_attributes=True)


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, session: AsyncSession = Depends(get_db)):
    movie = await session.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    await session.delete(movie)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    session: AsyncSession = Depends(get_db),
):
    movie = await session.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    data = payload.model_dump(exclude_unset=True)

    if "name" in data and data["name"] is not None and len(data["name"]) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
    if "score" in data and data["score"] is not None:
        try:
            score_val = float(data["score"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
        if not (0 <= score_val <= 100):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
    if "budget" in data and data["budget"] is not None:
        try:
            budget_val = float(data["budget"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
        if budget_val < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
    if "revenue" in data and data["revenue"] is not None:
        try:
            revenue_val = float(data["revenue"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
        if revenue_val < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")

    for field, value in data.items():
        setattr(movie, field, value)

    await session.commit()

    return {"detail": "Movie updated successfully."}
