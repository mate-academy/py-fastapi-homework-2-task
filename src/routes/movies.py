from typing import List, Optional
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
    MoviesListResponse,
    MovieUpdate,
    SimpleIdName,
    CountryOut,
)

router = APIRouter()


# Helper: strip api prefix so links look like README example (/theater/...)
def _make_base_path(request: Request) -> str:
    #path = request.url.path
    # remove api version prefix if present (e.g. /api/v1)
    #if path.startswith("/api/v1"):
    #    path = path[len("/api/v1") :]
    #return path
    return request.url.path.removeprefix("/api/v1")


@router.get("/movies/", response_model=MoviesListResponse)
async def list_movies(
    request: Request,
    page: conint(ge=1) = 1,
    per_page: conint(ge=1, le=20) = 10,
    db: AsyncSession = Depends(get_db),
):
    # validate params
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="page must be >= 1"
        )
    if not (1 <= per_page <= 20):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="per_page must be between 1 and 20",
        )

    # total items
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

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    # build prev/next links. Use path without /api/v1 prefix for compatibility with README
    base_path = _make_base_path(request)
    # ensure trailing slash on base path
    if not base_path.endswith("/"):
        base_path = base_path + "/"

    def make_link(p: int, pp: int) -> str:
        return f"{base_path}?page={p}&per_page={pp}"

    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    if page > 1:
        prev_page = make_link(page - 1, per_page)
    if page < total_pages:
        next_page = make_link(page + 1, per_page)

    # convert to MovieOut via Pydantic (orm_mode)
    movies_out = [MovieOut.from_orm(m) for m in movies]

    return MoviesListResponse(
        movies=movies_out,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", status_code=status.HTTP_201_CREATED, response_model=MovieOut)
async def create_movie(
    payload: MovieCreate, db: AsyncSession = Depends(get_db)
):
    # duplicate check
    dup_stmt = select(MovieModel).filter(
        MovieModel.name == payload.name, MovieModel.date == payload.date
    )
    dup = (await db.execute(dup_stmt)).scalars().first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.",
        )

    # Country: try to get by code (case-sensitive in model: code stored as provided)
    country_stmt = select(CountryModel).filter(CountryModel.code == payload.country)
    country = (await db.execute(country_stmt)).scalars().first()
    if not country:
        country = CountryModel(code=payload.country, name=None)
        db.add(country)
        await db.flush()  # to get country.id

    # Create or get genres
    genres_models = []
    for g_name in payload.genres:
        g_stmt = select(GenreModel).filter(GenreModel.name == g_name)
        g = (await db.execute(g_stmt)).scalars().first()
        if not g:
            g = GenreModel(name=g_name)
            db.add(g)
            await db.flush()
        genres_models.append(g)

    # actors
    actors_models = []
    for a_name in payload.actors:
        a_stmt = select(ActorModel).filter(ActorModel.name == a_name)
        a = (await db.execute(a_stmt)).scalars().first()
        if not a:
            a = ActorModel(name=a_name)
            db.add(a)
            await db.flush()
        actors_models.append(a)

    # languages
    languages_models = []
    for l_name in payload.languages:
        l_stmt = select(LanguageModel).filter(LanguageModel.name == l_name)
        l = (await db.execute(l_stmt)).scalars().first()
        if not l:
            l = LanguageModel(name=l_name)
            db.add(l)
            await db.flush()
        languages_models.append(l)

    # create movie
    try:
        movie = MovieModel(
            name=payload.name,
            date=payload.date,
            score=float(payload.score),
            overview=payload.overview,
            status=payload.status,
            budget=Decimal(str(payload.budget)),
            revenue=float(payload.revenue),
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

    # build response country object
    # return MovieOut.from_orm(movie)
    # reload movie with relationships for response
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
    return None  # 204 No Content


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

    # validate via pydantic has already been performed on payload
    data = payload.dict(exclude_unset=True)

    # prevent duplicate name+date if both provided or one provided and clashes with existing other movie
    new_name = data.get("name", movie.name)
    new_date = data.get("date", movie.date)

    # check duplicate with other movie
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

    # apply updates
    for field, value in data.items():
        if field in ("budget",):
            # convert to Decimal to match DECIMAL db type
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
