from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select
)
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from database import (
    MovieModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    ActorModel
)
from schemas import (
    MovieReadSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema
)
from paginations import (
    get_paginated_query
)


async def get_or_create(db: AsyncSession, model, field: str, value: str):
    query = select(model).where(getattr(model, field) == value)
    result = await db.execute(query)
    instance = result.scalar_one_or_none()

    if not instance:
        instance = model(**{field: value})
        db.add(instance)
        await db.commit()
        await db.refresh(instance)

    return instance


async def read_movies(db: AsyncSession, page: int = None, per_page: int = None):
    """One of CRUD operation R-Read"""
    movies = select(MovieModel).order_by(MovieModel.id.desc())

    if page and per_page:
        movies = await get_paginated_query(
            query=movies, page=page, per_page=per_page
        )
    result = await db.execute(movies)

    return result.scalars().all()


async def create_movies(movie: MovieCreateSchema, db: AsyncSession):
    """One of CRUD operations C-Create Movie
     and automatically connects to relative models"""
    # Check if movie does not exist
    existing = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
            status_code=409
        )

    country = await get_or_create(
        db=db, model=CountryModel, field="code", value=movie.country
    )
    genres = [
        await get_or_create(db, GenreModel, "name", genre)
        for genre in movie.genres
    ]
    actors = [
        await get_or_create(db, ActorModel, "name", actor)
        for actor in movie.actors
    ]
    languages = [
        await get_or_create(db, LanguageModel, "name", language)
        for language in movie.languages
    ]
    new_movie = MovieModel(
        **movie.model_dump(exclude={"genres", "country", "actors", "languages"}),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(
        new_movie,
        attribute_names=["country", "genres", "actors", "languages"]
    )

    return new_movie


async def read_movie(db: AsyncSession, movie_id: int) -> None | MovieModel:
    movie = await db.execute(
        select(MovieModel).where(
            MovieModel.id == movie_id
        ).options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages)
        )
    )

    return movie.scalar_one_or_none()


async def remove_movie(db: AsyncSession, movie_id: int) -> None | MovieModel:
    movie = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = movie.scalar_one_or_none()

    if movie:
        await db.delete(movie)
        await db.commit()
        return movie


async def update_movie(
        db: AsyncSession, movie_sch: MovieUpdateSchema, movie_id: int
) -> MovieModel | None:
    """Update MovieModel instance with a given `movie_id`. If movie exist returns movie either None"""
    movie = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = movie.scalar_one_or_none()
    if not movie:
        return None

    movie_data = movie_sch.model_dump(exclude_unset=True)
    for key, value in movie_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return movie
