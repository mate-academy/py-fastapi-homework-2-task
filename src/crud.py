from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from fastapi import HTTPException
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import FilmCreate, FilmUpdate


async def get_or_create(session: AsyncSession, model, **kwargs):
    result = await session.execute(select(model).filter_by(**kwargs))
    instance = result.scalars().first()
    if instance:
        return instance
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()
    return instance


async def create_film(session: AsyncSession, film_data: FilmCreate):
    query = select(MovieModel).where(
        MovieModel.name == film_data.name,
        MovieModel.date == film_data.date
    )
    if (await session.execute(query)).scalar():
        raise HTTPException(
            409,
            f"A movie with the name '{film_data.name}' and release date '{film_data.date}' already exists."
        )

    country = await get_or_create(session, CountryModel, code=film_data.country)
    genres = [await get_or_create(session, GenreModel, name=g) for g in film_data.genres]
    actors = [await get_or_create(session, ActorModel, name=a) for a in film_data.actors]
    languages = [await get_or_create(session, LanguageModel, name=a) for a in film_data.languages]

    movie = MovieModel(
        name=film_data.name,
        date=film_data.date,
        score=film_data.score,
        overview=film_data.overview,
        status=film_data.status,
        budget=film_data.budget,
        revenue=film_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    session.add(movie)
    await session.commit()
    await session.refresh(movie)

    query = (
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    result = await session.execute(query)
    return result.scalar_one()


async def get_paginated_movies(session: AsyncSession, page: int, per_page: int):
    total_items = (await session.execute(select(func.count()).select_from(MovieModel))).scalar()
    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages and total_items > 0:
        raise HTTPException(404, "No movies found.")

    offset = (page - 1) * per_page
    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(query)
    return result.scalars().all(), total_items, total_pages


async def get_film_by_id(session: AsyncSession, film_id: int):
    query = (
        select(MovieModel)
        .where(MovieModel.id == film_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    result = await session.execute(query)
    film = result.scalar_one_or_none()
    if not film:
        raise HTTPException(404, detail="Movie with the given ID was not found.")
    return film


async def delete_film(session: AsyncSession, film_id: int):
    film = await get_film_by_id(session, film_id)
    await session.delete(film)
    await session.commit()


async def update_film(session: AsyncSession, film_id: int, data: FilmUpdate):
    film = await get_film_by_id(session, film_id)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(film, field, value)
    try:
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(400, detail="Invalid input data.")
    query = (
        select(MovieModel)
        .where(MovieModel.id == film.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    result = await session.execute(query)
    return result.scalar_one()
