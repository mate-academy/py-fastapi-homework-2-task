from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import math

from database import get_db
from database.models import MovieModel, ActorModel, GenreModel, CountryModel, LanguageModel
from schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    MoviePaginationResponse,
    MovieUpdateSuccessResponse
)

router = APIRouter(prefix="/movies", tags=["Movies"])


async def get_or_create_entities(db: AsyncSession, model_cls, names: List[str]):
    if not names:
        return []
    clean_names = list(set([n.strip() for n in names if n.strip()]))
    if not clean_names:
        return []

    query = select(model_cls).where(model_cls.name.in_(clean_names))
    result = await db.execute(query)
    existing_entities = result.scalars().all()
    existing_names = {e.name for e in existing_entities}

    new_entities = []
    for name in clean_names:
        if name not in existing_names:
            new_obj = model_cls(name=name)
            db.add(new_obj)
            new_entities.append(new_obj)

    if new_entities:
        await db.flush()

    return list(existing_entities) + new_entities


async def get_or_create_country(db: AsyncSession, code_str: str) -> Optional[CountryModel]:
    if not code_str or not code_str.strip():
        return None
    clean_code = code_str.strip()

    query = select(CountryModel).where(CountryModel.code == clean_code)
    result = await db.execute(query)
    country_obj = result.scalar_one_or_none()

    if not country_obj:
        country_obj = CountryModel(code=clean_code, name=clean_code)
        db.add(country_obj)
        await db.flush()

    return country_obj


# 1. GET ALL MOVIES
# src/routes/movies.py
@router.get("/", response_model=MoviePaginationResponse, status_code=status.HTTP_200_OK)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        search: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    count_query = select(func.count()).select_from(MovieModel)
    if search:
        count_query = count_query.where(MovieModel.name.ilike(f"%{search}%"))

    count_res = await db.execute(count_query)
    total_items = count_res.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")

    offset = (page - 1) * per_page

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    query = select(MovieModel)
    if search:
        query = query.where(MovieModel.name.ilike(f"%{search}%"))

    query = query.order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


# 2. CREATE MOVIE (Fixes the get_attribute_error using selectinload refresh strategy)
@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db)):
    duplicate_query = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date
    )
    dup_res = await db.execute(duplicate_query)
    if dup_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_in.name}' and release date "
                   f"'{movie_in.date.isoformat()}' already exists."
        )

    new_movie = MovieModel(
        name=movie_in.name,
        overview=movie_in.overview,
        date=movie_in.date,
        score=movie_in.score,
        budget=movie_in.budget if movie_in.budget is not None else 0.0,
        revenue=movie_in.revenue if movie_in.revenue is not None else 0.0,
        status=movie_in.status or "Released"
    )

    if movie_in.genres:
        new_movie.genres = await get_or_create_entities(db, GenreModel, movie_in.genres)
    if movie_in.actors:
        new_movie.actors = await get_or_create_entities(db, ActorModel, movie_in.actors)
    if movie_in.languages:
        new_movie.languages = await get_or_create_entities(db, LanguageModel, movie_in.languages)
    if movie_in.country:
        new_movie.country = await get_or_create_country(db, movie_in.country)

    db.add(new_movie)
    await db.commit()

    # Force loading of relations prior to returning response content to schema validator
    query = select(MovieModel).options(
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.country),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == new_movie.id)

    result = await db.execute(query)
    return result.scalar_one()


# 3. GET MOVIE DETAILS
@router.get("/{movie_id}/", response_model=MovieResponse, status_code=status.HTTP_200_OK)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).options(
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.country),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)

    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return movie


# 4. UPDATE MOVIE (PATCH)
@router.patch("/{movie_id}/", response_model=MovieUpdateSuccessResponse, status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int, movie_in: MovieUpdate, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).options(
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.country),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)

    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_in.model_dump(exclude_unset=True)

    genres_list = update_data.pop("genres", None)
    actors_list = update_data.pop("actors", None)
    country_str = update_data.pop("country", None)
    languages_list = update_data.pop("languages", None)

    for field, value in update_data.items():
        setattr(movie, field, value)

    if genres_list is not None:
        movie.genres = await get_or_create_entities(db, GenreModel, genres_list)
    if actors_list is not None:
        movie.actors = await get_or_create_entities(db, ActorModel, actors_list)
    if languages_list is not None:
        movie.languages = await get_or_create_entities(db, LanguageModel, languages_list)
    if country_str is not None:
        movie.country = await get_or_create_country(db, country_str)

    await db.commit()
    return {"detail": "Movie updated successfully."}


# 5. DELETE MOVIE
@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
