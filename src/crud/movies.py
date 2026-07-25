from typing import Iterable, Type

from sqlalchemy import func, select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, Base
from schemas.movies import MovieAddSchema, MovieUpdateSchema


class AlreadyExists(Exception):
    pass


async def read_all_movies(
    session: AsyncSession, skip: int = 0, limit: int = 10
) -> tuple[list[MovieModel], int]:
    count = await session.scalar(func.count(MovieModel.id))
    stmt = select(MovieModel).order_by(MovieModel.id.desc()).offset(skip).limit(limit)
    movies = await session.scalars(stmt)

    count = int(count)
    movies = list(movies.all())
    return movies, count


async def create_movie(session: AsyncSession, movie: MovieAddSchema) -> MovieModel:
    def combine_existing_seq(seq: list, existing: Iterable, _class: Type[Base]) -> list:
        dct = {obj.name: obj for obj in existing}
        return [dct.get(name) or _class(name=name) for name in seq]

    orm_movie = MovieModel(
        **movie.model_dump(exclude={"country", "genres", "actors", "languages"})
    )
    country_obj = await session.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    country_obj = country_obj or CountryModel(code=movie.country)
    orm_movie.country = country_obj
    fields = {
        "genres": GenreModel,
        "actors": ActorModel,
        "languages": LanguageModel,
    }

    for key, value in fields.items():
        attribute = getattr(movie, key)
        db_existing = await session.scalars(
            select(value).where(value.name.in_(attribute))
        )
        setattr(
            orm_movie, key, combine_existing_seq(attribute, db_existing.all(), value)
        )

    session.add(orm_movie)
    try:
        await session.commit()
        return orm_movie
    except IntegrityError:
        raise AlreadyExists()


async def read_one_movie(session: AsyncSession, movie_id: int) -> MovieModel | None:
    movie = await session.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.genres),
        )
    )
    return movie


async def delete_movie(session: AsyncSession, movie_id: int) -> int:
    result = await session.execute(delete(MovieModel).where(MovieModel.id == movie_id))
    await session.commit()
    return result.rowcount


async def update_movie(
    session: AsyncSession, movie_id: int, movie: MovieUpdateSchema
) -> int:
    result = await session.execute(
        update(MovieModel)
        .values(**movie.model_dump(exclude_unset=True))
        .where(MovieModel.id == movie_id)
    )
    await session.commit()
    return result.rowcount
