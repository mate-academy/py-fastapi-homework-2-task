from math import ceil
from typing import Annotated
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from database import get_db, models, MovieModel
from database.models import GenreModel, ActorModel, LanguageModel, CountryModel

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    total_count = await db.scalar(select(func.count(models.MovieModel.id)))
    total_pages = ceil(total_count / per_page)

    offset = (page - 1) * per_page
    query = (
        select(models.MovieModel)
        .order_by(models.MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = (
        f"{base_url}?page={page - 1}&per_page={per_page}"
        if (page > 1)
        else None
    )
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if (page < total_pages)
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_count,
    }


async def get_or_create_genres(
    db: Annotated[AsyncSession, Depends(get_db)], genres_names: list[str]
):
    genres = []
    for name in genres_names:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == name)
        )
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
        genres.append(genre)
    return genres


async def get_or_create_actors(
    db: Annotated[AsyncSession, Depends(get_db)], actor_names: list[str]
):
    actors = []
    for name in actor_names:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == name)
        )
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
        actors.append(actor)
    return actors


async def get_or_create_languages(
    db: Annotated[AsyncSession, Depends(get_db)], language_names: list[str]
):
    languages = []
    for name in language_names:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
        languages.append(language)
    return languages


async def get_country_by_name(
    db: Annotated[AsyncSession, Depends(get_db)], country_code: str
):
    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    if not country:
        country = CountryModel(code=country_code)
        db.add(country)
    return country


@router.post(
    "/movies/", response_model=schemas.MovieDetailSchema, status_code=201
)
async def create_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_data: schemas.MovieCreateSchema,
):
    genre_objects = await get_or_create_genres(db, movie_data.genres)
    actor_objects = await get_or_create_actors(db, movie_data.actors)
    language_objects = await get_or_create_languages(db, movie_data.languages)
    country = await get_country_by_name(db, movie_data.country)
    movie_exist = await db.scalar(
        select(MovieModel).where(
            and_(
                MovieModel.name == movie_data.name,
                MovieModel.date == movie_data.date,
            )
        )
    )

    if movie_exist:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )
    db_movie = models.MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genre_objects,
        actors=actor_objects,
        languages=language_objects,
    )

    try:
        db.add(db_movie)
        await db.flush()
        await db.commit()
        await db.refresh(db_movie)
    except IntegrityError:
        await db.rollback()

    stmt = (
        select(models.MovieModel)
        .options(
            selectinload(models.MovieModel.country),
            selectinload(models.MovieModel.genres),
            selectinload(models.MovieModel.actors),
            selectinload(models.MovieModel.languages),
        )
        .where(models.MovieModel.id == db_movie.id)
    )
    result = await db.execute(stmt)
    final_movie = result.scalar_one()

    return final_movie


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def movie_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int = Path(..., gt=0, le=2147483647),
):
    movie = await db.scalar(
        select(models.MovieModel)
        .options(
            selectinload(models.MovieModel.country),
            selectinload(models.MovieModel.genres),
            selectinload(models.MovieModel.actors),
            selectinload(models.MovieModel.languages),
        )
        .where(models.MovieModel.id == movie_id)
    )
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int = Path(..., gt=0, le=2147483647),
):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_data: schemas.MovieUpdateSchema,
    movie_id: int = Path(..., gt=0, le=2147483647),
):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    update_data = movie_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.flush()
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return JSONResponse(
        status_code=200, content={"detail": "Movie updated successfully."}
    )
