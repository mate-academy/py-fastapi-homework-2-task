from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from schemas.movies import MovieCreateRequestSchema, MovieUpdateSchema
from crud.common import get_or_create_by_field
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    MovieModel,
    LanguageModel,
)


async def get_movies(
    db: AsyncSession,
    skip: int,
    limit: int,
):
    result = await db.scalars(
        select(MovieModel).offset(skip).limit(limit).order_by(MovieModel.id.desc())
    )

    return list(result.all())


async def get_movie(db: AsyncSession, movie_id: int):
    return await db.scalar(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )


async def create_movie(db: AsyncSession, data: MovieCreateRequestSchema):
    [country] = await get_or_create_by_field(db, CountryModel, "code", [data.country])
    genres = await get_or_create_by_field(db, GenreModel, "name", data.genres)
    actors = await get_or_create_by_field(db, ActorModel, "name", data.actors)
    languages = await get_or_create_by_field(db, LanguageModel, "name", data.languages)
    movie = MovieModel(
        **data.model_dump(exclude={"country", "genres", "actors", "languages"}),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()

    return await get_movie(db, movie.id)


async def get_movie_by_name_date(db: AsyncSession, name, date):
    film = await db.scalar(
        select(MovieModel).where(MovieModel.name == name, MovieModel.date == date)
    )
    return film


async def delete_movie(db: AsyncSession, movie: MovieModel):
    await db.delete(movie)
    await db.commit()


async def update_movie(db: AsyncSession, movie: MovieModel, data: MovieUpdateSchema):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)
    await db.commit()
