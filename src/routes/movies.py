import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from schemas.movies import (
    MovieSimpleResponseSchema,
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageResponseSchema
)

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from datetime import datetime, timedelta


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    movies = result.scalars().all()
    total_count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_count_result.scalar()
    total_pages = math.ceil(total_items / per_page)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=[MovieSimpleResponseSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    if len(movie.name) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.date > datetime.now().date() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.score < 0 or movie.score > 100:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.budget < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    if existing_movie.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country_result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)

    genres = []
    for genre_name in movie.genres:
        genre_result = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor_result = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
        actor = actor_result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language_result = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
        language = language_result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
        languages.append(language)

    await db.flush()

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )
    db.add(new_movie)
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    movie_with_relations = result.scalar_one()

    return MovieDetailResponseSchema.model_validate(movie_with_relations)


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return MovieDetailResponseSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=200, response_model=MessageResponseSchema)
async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    if movie.score is not None and (movie.score < 0 or movie.score > 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.budget is not None and movie.budget < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if movie.revenue is not None and movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    existing_movie = result.scalar_one_or_none()

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie.name is not None:
        existing_movie.name = movie.name
    if movie.date is not None:
        existing_movie.date = movie.date
    if movie.score is not None:
        existing_movie.score = movie.score
    if movie.overview is not None:
        existing_movie.overview = movie.overview
    if movie.status is not None:
        existing_movie.status = movie.status
    if movie.budget is not None:
        existing_movie.budget = movie.budget
    if movie.revenue is not None:
        existing_movie.revenue = movie.revenue
    await db.commit()
    return {"detail": "Movie updated successfully."}
