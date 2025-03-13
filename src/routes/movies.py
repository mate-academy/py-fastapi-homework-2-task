import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import Annotated, List

from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
from schemas.movies import ReadMoviesList, ReadMovieDetail, MovieCreate, MovieUpdate

router = APIRouter()


@router.get("/movies/", response_model=ReadMoviesList)
async def read_movies(
        db: AsyncSession = Depends(get_db),
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    query = select(MovieModel).offset(
        per_page * (page - 1)
    ).limit(per_page).order_by(
        MovieModel.id.desc()
    )

    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    query = select(func.count()).select_from(MovieModel)
    total_items_result = await db.execute(query)
    total_items = total_items_result.scalar()
    total_pages = (total_items // per_page) + 1

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=ReadMovieDetail, status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie: MovieCreate,
        db: AsyncSession = Depends(get_db),
):
    query = select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    )
    result = await db.execute(query)
    movie_model = result.scalars().first()

    if movie_model:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}'"
                   f" and release date '{movie.date}' already exists."
        )

    movie_model = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue
    )

    query = select(CountryModel).where(CountryModel.code == movie.country)
    result = await db.execute(query)
    country_model = result.scalar_one_or_none()
    if not country_model:
        country_model = CountryModel(code=movie.country)
    movie_model.country = country_model

    for genre in movie.genres:
        query = select(GenreModel).where(GenreModel.name == genre)
        result = await db.execute(query)
        _genre = result.scalar_one_or_none()
        if not _genre:
            _genre = GenreModel(name=genre)
        movie_model.genres.append(_genre)

    for actor in movie.actors:
        query = select(ActorModel).where(ActorModel.name == actor)
        result = await db.execute(query)
        _actor = result.scalar_one_or_none()
        if not _actor:
            _actor = ActorModel(name=actor)
        movie_model.actors.append(_actor)

    for language in movie.languages:
        query = select(LanguageModel).where(LanguageModel.name == language)
        result = await db.execute(query)
        _language = result.scalar_one_or_none()
        if not _language:
            _language = LanguageModel(name=language)
        movie_model.languages.append(_language)

    db.add(movie_model)
    await db.commit()
    await db.refresh(movie_model)

    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_model.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = await db.execute(query)
    movie = result.unique().scalar_one_or_none()
    return movie


@router.get("/movies/{movie_id}/", response_model=ReadMovieDetail)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = (await db.execute(query)).unique()
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
        movie_id: int,
        movie: MovieUpdate,
        db: AsyncSession = Depends(get_db),
):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie_model = result.scalar_one_or_none()
    if not movie_model:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    data = movie.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(movie_model, field, value)

    db.add(movie_model)
    await db.commit()
    await db.refresh(movie_model)

    return {
        "detail": "Movie updated successfully.",
    }
