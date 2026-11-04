import math
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateRequestSchema,
    MovieUpdateRequestSchema,
    MovieDetailSchema
)

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/movies/", response_model=MovieListResponseSchema, status_code=200)
async def get_movies(
        db: SessionDep,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10
):
    total_items_res = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_res.scalar()

    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(payload: MovieCreateRequestSchema, db: SessionDep):
    existing_res = await db.execute(
        select(MovieModel).filter(
            MovieModel.name == payload.name,
            MovieModel.date == payload.date
        )
    )
    if existing_res.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists."
        )

    country_res = await db.execute(select(CountryModel).filter(CountryModel.code == payload.country))
    country = country_res.scalar()
    if not country:
        country = CountryModel(code=payload.country, name=None)
        db.add(country)
        await db.flush()

    genres_list = []
    for g_name in payload.genres:
        res = await db.execute(select(GenreModel).filter(GenreModel.name == g_name))
        genre = res.scalar() or GenreModel(name=g_name)
        genres_list.append(genre)

    actors_list = []
    for a_name in payload.actors:
        res = await db.execute(select(ActorModel).filter(ActorModel.name == a_name))
        actor = res.scalar() or ActorModel(name=a_name)
        actors_list.append(actor)

    languages_list = []
    for l_name in payload.languages:
        res = await db.execute(select(LanguageModel).filter(LanguageModel.name == l_name))
        lang = res.scalar() or LanguageModel(name=l_name)
        languages_list.append(lang)

    await db.flush()

    new_movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country_id=country.id,
        genres=genres_list,
        actors=actors_list,
        languages=languages_list
    )

    try:
        db.add(new_movie)
        await db.commit()

        stmt = (
            select(MovieModel)
            .options(
                joinedload(MovieModel.country),
                joinedload(MovieModel.genres),
                joinedload(MovieModel.actors),
                joinedload(MovieModel.languages),
            )
            .filter(MovieModel.id == new_movie.id)
        )
        refresh_res = await db.execute(stmt)
        new_movie = refresh_res.unique().scalar_one()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return new_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema, status_code=200)
async def get_movie_by_id(movie_id: int, db: SessionDep):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .filter(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.unique().scalar()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: SessionDep):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalar()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(movie_id: int, payload: MovieUpdateRequestSchema, db: SessionDep):
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalar()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return {"detail": "Movie updated successfully."}

    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
