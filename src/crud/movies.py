from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database.models import (
    MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel,
)
from schemas.movies import MovieCreateRequest, MovieUpdateRequest


async def get_movies_list(db: AsyncSession, offset: int = 0, limit: int = 100):
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def get_detail_movie(db: AsyncSession, movie_id: int):
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
    return result.scalar_one_or_none()


async def count_movies(db: AsyncSession):
    result = await db.execute(select(func.count(MovieModel.id)))
    return result.scalar()


async def create_movie(db: AsyncSession, movie_data: MovieCreateRequest):
    stmt = select(MovieModel).filter(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    required_fields = ["name", "date", "score", "overview", "status", "budget", "revenue", "country", "genres",
                       "actors", "languages"]
    for field in required_fields:
        if getattr(movie_data, field) is None:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    country = await db.execute(select(CountryModel).filter(CountryModel.code == movie_data.country))
    country = country.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie_data.country)
        db.add(country)

    genres = []
    for genre_name in movie_data.genres:
        genre = await db.execute(select(GenreModel).filter(GenreModel.name == genre_name))
        genre = genre.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = await db.execute(select(ActorModel).filter(ActorModel.name == actor_name))
        actor = actor.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = await db.execute(select(LanguageModel).filter(LanguageModel.name == language_name))
        language = language.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
        languages.append(language)

    new_movie = MovieModel(
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
    db.add(new_movie)

    await db.commit()
    await db.refresh(new_movie)

    stmt = select(MovieModel).filter(MovieModel.id == new_movie.id).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    )
    result = await db.execute(stmt)
    new_movie = result.scalar_one()

    return new_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


async def update_movie(db: AsyncSession, movie_id: int, data: MovieUpdateRequest):
    result = await db.execute(
        select(MovieModel).filter(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
