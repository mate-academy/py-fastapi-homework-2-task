from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieStatusEnum,
)
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    result = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        await db.commit()
        await db.refresh(country)

    genres = []
    for genre_name in movie.genres:
        result = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.commit()
            await db.refresh(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        result = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.commit()
            await db.refresh(actor)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == language_name)
        )
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.commit()
            await db.refresh(language)
        languages.append(language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=MovieStatusEnum(movie.status),
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return new_movie


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_delete = result.scalar_one_or_none()
    if not movie_to_delete:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie_to_delete)
    await db.commit()


async def update_movie(db: AsyncSession, movie: MovieUpdateSchema, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie_to_update = result.scalar_one_or_none()
    if not movie_to_update:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    data = movie.model_dump(exclude_unset=True)
    if (
        "score" in data
        and data["score"] is not None
        and not (0 <= data["score"] <= 100)
    ):
        raise HTTPException(status_code=400, detail="Invalid score.")
    if "budget" in data and data["budget"] is not None and data["budget"] < 0:
        raise HTTPException(status_code=400, detail="Invalid budget.")
    if "revenue" in data and data["revenue"] is not None and data["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Invalid revenue.")

    for key, value in data.items():
        setattr(movie_to_update, key, value)

    await db.commit()
    await db.refresh(movie_to_update)
