from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from src.schemas import MovieCreateSchema, MovieUpdateSchema
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status


async def get_or_create_country(session: AsyncSession, code: str) -> CountryModel:
    result = await session.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalars().first()
    if country:
        return country
    country = CountryModel(code=code)
    session.add(country)
    await session.flush()
    return country


async def get_or_create_entities(session: AsyncSession, model, names: list[str]) -> list:
    result = await session.execute(select(model).where(model.name.in_(names)))
    existing = {obj.name: obj for obj in result.scalars().all()}
    entities = []
    for name in names:
        if name in existing:
            entities.append(existing[name])
        else:
            obj = model(name=name)
            session.add(obj)
            await session.flush()
            entities.append(obj)
    return entities


async def create_movie(session: AsyncSession, movie_data: MovieCreateSchema) -> MovieModel:
    # Check for duplicate
    result = await session.execute(
        select(MovieModel).where(
            and_(
                MovieModel.name == movie_data.name,
                MovieModel.date == movie_data.date
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # Get or create related entities
    country = await get_or_create_country(session, movie_data.country)
    genres = await get_or_create_entities(session, GenreModel, movie_data.genres)
    actors = await get_or_create_entities(session, ActorModel, movie_data.actors)
    languages = await get_or_create_entities(session, LanguageModel, movie_data.languages)

    # Create movie
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
        languages=languages
    )

    session.add(movie)
    await session.commit()
    await session.refresh(movie, [
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ])

    return movie

async def get_movies(session: AsyncSession, skip: int = 0, limit: int = 10):
    result = await session.execute(select(MovieModel).offset(skip).limit(limit))
    movies = result.scalars().all()

    total_result = await session.execute(select(MovieModel))
    total = len(total_result.scalars().all())

    return movies, total

async def get_movie_by_id(session: AsyncSession, movie_id: int):
    result = await session.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalars().first()
    return movie


async def update_movie(session: AsyncSession, movie_id: int, movie_data: MovieUpdateSchema):
    result = await session.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        return None

    for field, value in movie_data.dict(exclude_unset=True).items():
        if field == "genre_ids":
            genres = await session.execute(select(GenreModel).where(GenreModel.id.in_(value)))
            movie.genres = genres.scalars().all()
        elif field == "actor_ids":
            actors = await session.execute(select(ActorModel).where(ActorModel.id.in_(value)))
            movie.actors = actors.scalars().all()
        elif field == "language_ids":
            languages = await session.execute(select(LanguageModel).where(LanguageModel.id.in_(value)))
            movie.languages = languages.scalars().all()
        elif field == "country_id":
            country = await session.get(CountryModel, value)
            movie.country = country
        else:
            setattr(movie, field, value)
    await session.commit()
    await session.refresh(movie)
    return movie

async def delete_movie(session: AsyncSession, movie_id: int):
    result = await session.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        return False
    await session.delete(movie)
    await session.commit()
    return True