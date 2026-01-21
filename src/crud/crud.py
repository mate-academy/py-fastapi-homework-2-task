from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from src.schemas.movies import MovieCreateSchema, MovieUpdateSchema, MovieDetailResponseSchema


async def get_movies(
    db: AsyncSession,
    page: int,
    per_page: int,
):
    offset = (page - 1) * per_page

    movies_stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    result = await db.execute(movies_stmt)
    movies = result.unique().scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    total_pages = ceil(total_items / per_page) if total_items else 0

    return {
        "movies": movies,
        "total_items": total_items,
        "total_pages": total_pages,
    }


async def get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel:
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


async def create_movie(
    db: AsyncSession,
    movie_data: MovieCreateSchema,
) -> MovieModel:

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie_data.country)
    )
    if not country:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in movie_data.genres:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == name)
        )
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in movie_data.actors:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == name)
        )
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in movie_data.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=float(movie_data.budget),
        revenue=float(movie_data.revenue),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(movie)

    try:
        await db.commit()
        await db.refresh(movie, attribute_names=["country", "genres", "actors", "languages"])
        return movie

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )


async def update_movie(
    db: AsyncSession,
    movie_id: int,
    movie_data: MovieUpdateSchema,
):
    movie = await get_movie_by_id(db, movie_id)

    update_data = movie_data.model_dump(exclude_unset=True)

    if not update_data:
        return

    for field, value in update_data.items():
        if field in ("budget", "revenue") and value is not None:
            value = float(value)
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )


async def delete_movie(db: AsyncSession, movie_id: int):
    movie = await get_movie_by_id(db, movie_id)
    await db.delete(movie)
    await db.commit()
