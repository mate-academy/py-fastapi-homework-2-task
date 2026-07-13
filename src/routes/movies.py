from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieUpdateSchema,
    MessageSchema,
    MovieCreateSchema,
)

router = APIRouter()


def validate_movie_date(movie_date: date) -> None:
    max_date = date.today() + timedelta(days=365)

    if movie_date > max_date:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(
        select(func.count(MovieModel.id))
    )

    total_pages = (total_items + per_page - 1) // per_page

    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=[
            MovieListItemSchema(
                id=movie.id,
                name=movie.name,
                date=movie.date,
                score=movie.score,
                overview=movie.overview,
            )
            for movie in movies
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
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

    result = await db.execute(stmt)
    movie = result.unique().scalars().first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=204,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    response_model=MessageSchema,
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    if movie_data.date is not None:
        validate_movie_date(movie_data.date)

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=201,
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    validate_movie_date(movie_data.date)

    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    country = await db.scalar(
        select(CountryModel).where(
            CountryModel.code == movie_data.country
        )
    )

    if country is None:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        await db.flush()

    genres = []
    for genre_name in movie_data.genres:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        if genre is None:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        if actor is None:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == language_name)
        )
        if language is None:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()
        languages.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )

    return result.unique().scalars().first()
