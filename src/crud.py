from sqlalchemy import func
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import MovieModel
from schemas.movies import MovieCreate, MovieUpdate, MovieList
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


async def create_movie(db: AsyncSession, movie: MovieCreate) -> MovieModel:
    # Check duplicate movie
    result = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ))
    existing_movie = result.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(status_code=409,
                            detail=f"A movie with the name '{movie.name}'"
                                   f" and release date '{movie.date}' already exists.")
    # Create movie and check entity linking (country, genres, actors, languages)
    # Country
    country_result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()
    # Genres
    genres = []
    for genre_name in movie.genres:
        genre_result = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # Actors
    actors = []
    for actor_name in movie.actors:
        actor_result = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
        actor = actor_result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # Language
    languages = []
    for language_name in movie.languages:
        language_result = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
        language = language_result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()
        languages.append(language)

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
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    created_movie = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    return created_movie.scalar_one()


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel)
                              .where(MovieModel.id == movie_id)
                              .options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ))
    movie = result.scalar_one_or_none()
    return movie


async def get_movies(db: AsyncSession, page: int, per_page: int) -> tuple[list[MovieModel], int]:
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset).limit(per_page)
    )
    movies = result.scalars().all()
    result = await db.execute(select(func.count(MovieModel.id)))
    total_items = result.scalar_one_or_none()
    return movies, total_items


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    movie_data = movie.model_dump(exclude_unset=True)
    for key, value in movie_data.items():
        setattr(db_movie, key, value)
    await db.commit()
    updated_movie = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return updated_movie.scalar_one()


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie
