from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas import MovieCreateSchema, MoviePatchSchema


async def get_movies(db: AsyncSession, offset: int, limit: int):
    result = await db.execute(
        select(MovieModel).offset(offset).limit(limit).order_by(MovieModel.id.desc())
    )
    return result.scalars().all()


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    return result.scalar_one_or_none()


async def create_movie(db: AsyncSession, data: MovieCreateSchema) -> MovieModel:
    duplicate_movi = select(MovieModel).where(
        MovieModel.name == data.name, MovieModel.date == data.date
    )
    result = await db.execute(duplicate_movi)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists.",
        )

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == data.country)
    )
    if not country:
        country = CountryModel(code=data.country)
        db.add(country)

    genres = []
    for genre_name in data.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for actor_name in data.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for lang_name in data.languages:
        lang = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == lang_name)
        )
        if not lang:
            lang = LanguageModel(name=lang_name)
            db.add(lang)
        languages.append(lang)

    new_movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return await get_movie_by_id(db, new_movie.id)


async def patch_movie(db: AsyncSession, movie_id: int, data: MoviePatchSchema) -> None:
    movie = await get_movie_by_id(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    try:
        if data.name is not None:
            movie.name = data.name
        if data.date is not None:
            movie.date = data.date
        if data.score is not None:
            movie.score = data.score
        if data.overview is not None:
            movie.overview = data.overview
        if data.status is not None:
            movie.status = data.status
        if data.budget is not None:
            movie.budget = data.budget
        if data.revenue is not None:
            movie.revenue = data.revenue

        await db.commit()

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")


async def delete_movie(db: AsyncSession, movie_id: int):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    await db.delete(movie)
    await db.commit()
    return movie
