from typing import Sequence

from sqlalchemy import select, func, desc, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


class MovieAlreadyExistsError(Exception):
    pass


async def get_all_movies(session: AsyncSession, page: int, per_page: int) -> tuple[Sequence[MovieModel], int]:
    offset = (page - 1) * per_page

    count_stmt = select(func.count(MovieModel.id))
    total_items = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    movies = result.scalars().all()

    return movies, total_items


async def get_movie_by_id(session: AsyncSession, movie_id: int) -> MovieModel | None:
    return await session.get(MovieModel, movie_id)


async def get_or_create(
        session: AsyncSession, model, **kwargs
):
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalars().first()
    if instance:
        return instance
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()
    return instance


async def create_movie(
        session: AsyncSession, movie_data: MovieCreateSchema
) -> MovieModel:
    stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date,
    )
    result = await session.execute(stmt)
    existing_movie = result.scalars().first()
    if existing_movie:
        raise MovieAlreadyExistsError(
            f"A movie with the name '{movie_data.name}' "
            f"and release date '{movie_data.date}' already exists."
        )

    country = await get_or_create(session, CountryModel, code=movie_data.country.upper())

    genres = [
        await get_or_create(session, GenreModel, name=genre_name)
        for genre_name in movie_data.genres
    ]
    actors = [
        await get_or_create(session, ActorModel, name=actor_name)
        for actor_name in movie_data.actors
    ]
    languages = [
        await get_or_create(session, LanguageModel, name=lang_name)
        for lang_name in movie_data.languages
    ]

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

    session.add(movie)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise MovieAlreadyExistsError(
            f"A movie with the name '{movie_data.name}' "
            f"and release date '{movie_data.date}' already exists."
        )

    await session.refresh(movie)
    return movie


async def delete_movie(session: AsyncSession, movie_id: int) -> bool:
    stmt = delete(MovieModel).where(MovieModel.id == movie_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

async def update_movie(
    session: AsyncSession, movie_id: int, movie_data: MovieUpdateSchema
) -> bool:
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie is None:
        return False

    update_data = movie_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    await session.commit()
    return True