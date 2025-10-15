from typing import List
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import conint

from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from database import get_db
from schemas.movies import (
    MovieCreate,
    MovieOut,
    MovieUpdate,
    MovieShortOut,
    MovieListResponseSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    page: conint(ge=1) = 1,
    per_page: conint(ge=1, le=20) = 10,
    db: AsyncSession = Depends(get_db),
):
    total_stmt = select(func.count()).select_from(MovieModel)
    total_res = await db.execute(total_stmt)
    total_items = int(total_res.scalar_one() or 0)

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    offset = (page - 1) * per_page
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    res = await db.execute(stmt)
    movies: List[MovieModel] = res.scalars().all()

    base_path = "/theater/movies/"

    def make_link(p: int, pp: int) -> str:
        return f"{base_path}?page={p}&per_page={pp}"

    # prev_idx = max(1, page - 1)
    # next_idx = min(total_pages, page + 1)

    # prev_page = make_link(prev_idx, per_page)
    # next_page = make_link(next_idx, per_page)
    prev_page = None if page == 1 else make_link(page - 1, per_page)
    next_page = None if page == total_pages else make_link(page + 1, per_page)

    movies_out = [MovieShortOut.from_orm(m) for m in movies]

    return MovieListResponseSchema(
        movies=movies_out,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", status_code=status.HTTP_201_CREATED, response_model=MovieOut)
async def create_movie(payload: MovieCreate, db: AsyncSession = Depends(get_db)):
    dup_stmt = select(MovieModel).filter(
        MovieModel.name == payload.name, MovieModel.date == payload.date
    )
    dup = (await db.execute(dup_stmt)).scalars().first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.",
        )

    country_stmt = select(CountryModel).filter(CountryModel.code == payload.country)
    country = (await db.execute(country_stmt)).scalars().first()
    if not country:
        country = CountryModel(code=payload.country, name=None)
        db.add(country)
        await db.flush()

    genres_models = []
    for g_name in payload.genres:
        g_stmt = select(GenreModel).filter(GenreModel.name == g_name)
        g = (await db.execute(g_stmt)).scalars().first()
        if not g:
            g = GenreModel(name=g_name)
            db.add(g)
            await db.flush()
        genres_models.append(g)

    actors_models = []
    for a_name in payload.actors:
        a_stmt = select(ActorModel).filter(ActorModel.name == a_name)
        a = (await db.execute(a_stmt)).scalars().first()
        if not a:
            a = ActorModel(name=a_name)
            db.add(a)
            await db.flush()
        actors_models.append(a)

    languages_models = []
    for l_name in payload.languages:
        l_stmt = select(LanguageModel).filter(LanguageModel.name == l_name)
        l = (await db.execute(l_stmt)).scalars().first()
        if not l:
            l = LanguageModel(name=l_name)
            db.add(l)
            await db.flush()
        languages_models.append(l)

    try:
        movie = MovieModel(
            name=payload.name,
            date=payload.date,
            score=float(payload.score),
            overview=payload.overview,
            status=payload.status,
            budget=int(payload.budget),
            revenue=int(payload.revenue),
            country=country,
            genres=genres_models,
            actors=actors_models,
            languages=languages_models,
        )
        db.add(movie)
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )

    stmt = (
        select(MovieModel)
        .filter(MovieModel.id == movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    res = await db.execute(stmt)
    movie_with_relations = res.scalars().first()

    return MovieOut.from_orm(movie_with_relations)


@router.get("/movies/{movie_id}/", response_model=MovieOut)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .filter(MovieModel.id == movie_id)
    )
    res = await db.execute(stmt)
    movie = res.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return MovieOut.from_orm(movie)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, payload: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    data = payload.dict(exclude_unset=True)
    new_name = data.get("name", movie.name)
    new_date = data.get("date", movie.date)

    dup_stmt = select(MovieModel).filter(
        MovieModel.name == new_name,
        MovieModel.date == new_date,
        MovieModel.id != movie.id,
    )
    dup = (await db.execute(dup_stmt)).scalars().first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{new_name}' and release date '{new_date}' already exists.",
        )

    for field, value in data.items():
        if field == "budget":
            setattr(movie, field, Decimal(str(value)))
        else:
            setattr(movie, field, value)

    try:
        db.add(movie)
        await db.commit()
        await db.refresh(movie)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )

    return {"detail": "Movie updated successfully."}
