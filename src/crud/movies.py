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
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        updated = False

        for field in ("name", "date", "score", "overview", "status", "budget", "revenue"):
            value = getattr(data, field)
            if value is not None:
                setattr(movie, field, value)
                updated = True

        if hasattr(data, "country") and data.country:
            country = await db.scalar(
                select(CountryModel).where(CountryModel.code == data.country)
            )
            if not country:
                country = CountryModel(code=data.country)
                db.add(country)
            movie.country = country
            updated = True

        if hasattr(data, "genres") and data.genres:
            genres = []
            for name in data.genres:
                genre = await db.scalar(select(GenreModel).where(GenreModel.name == name))
                if not genre:
                    genre = GenreModel(name=name)
                    db.add(genre)
                genres.append(genre)
            movie.genres = genres
            updated = True

        if hasattr(data, "actors") and data.actors:
            actors = []
            for name in data.actors:
                actor = await db.scalar(select(ActorModel).where(ActorModel.name == name))
                if not actor:
                    actor = ActorModel(name=name)
                    db.add(actor)
                actors.append(actor)
            movie.actors = actors
            updated = True

        if hasattr(data, "languages") and data.languages:
            langs = []
            for name in data.languages:
                lang = await db.scalar(select(LanguageModel).where(LanguageModel.name == name))
                if not lang:
                    lang = LanguageModel(name=name)
                    db.add(lang)
                langs.append(lang)
            movie.languages = langs
            updated = True

        if updated:
            await db.commit()
        else:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def delete_movie(db: AsyncSession, movie_id: int):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        return None

    await db.delete(movie)
    await db.commit()
    return movie
