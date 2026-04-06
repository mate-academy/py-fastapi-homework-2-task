import asyncio

from collections.abc import Iterable
from typing import Tuple, List, Any, Optional
from functools import wraps

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, insert, ScalarResult, delete, update
from sqlalchemy.orm import selectinload

from database.models import (
    Base as BaseModel,
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import MovieDetailRequestSchema, MoviePatchSchema


def commit_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = kwargs.get("db") or next(
            (arg for arg in args if isinstance(arg, AsyncSession)), None
        )
        if not db:
            raise ValueError("Session not found")

        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            await db.rollback()
            raise e
        else:
            await db.commit()
            return result

    return wrapper


async def get_list_movies_with_pagination_and_count(
    db: AsyncSession, rows: Iterable[str], offset: int, limit: int
) -> Tuple[List[MovieModel], int] | Tuple[None, None]:
    stmt = (
        select(
            *[field for row in rows if (field := getattr(MovieModel, row, None))],
            func.count(MovieModel.id).over().label("total_items"),
        )
        .offset(offset)
        .limit(limit)
        .order_by(desc(MovieModel.id))
    )
    result = (await db.execute(stmt)).all()
    return (result, result[0][-1]) if result else (None, None)


@commit_decorator
async def get_or_create_default_objects(
    db: AsyncSession, model: BaseModel, field_to_search: str, filter_in: Iterable[str]
) -> Iterable[BaseModel]:
    """
    A write operation can be performed
    if the model has a single field
    that is equal to the field_to_search variable.
    """
    unique_filter = frozenset(filter_in)

    objects = (
        await db.scalars(
            select(model).where(getattr(model, field_to_search).in_(unique_filter))
        )
    ).all()
    if not objects or len(objects) < len(filter_in):
        founded_objects_set = frozenset(
            getattr(obj, field_to_search) for obj in objects
        )
        objects_to_create = unique_filter.difference(founded_objects_set)

        try:
            result = (
                (
                    await db.execute(
                        insert(model).returning(model),
                        ({field_to_search: field} for field in objects_to_create),
                    )
                )
                .scalars()
                .all()
            )
        except IntegrityError:
            ...
        else:
            return *objects, *result
    return objects


@commit_decorator
async def get_or_create_country(db: AsyncSession, country_code: str) -> CountryModel:
    object_ = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    if not object_:
        try:
            new_object = (
                await db.execute(
                    insert(CountryModel)
                    .values(code=country_code)
                    .returning(CountryModel),
                )
            ).scalar_one()
        except IntegrityError:
            ...
        else:
            return new_object
    return object_


@commit_decorator
async def create_new_movie(
    db: AsyncSession,
    movie: MovieDetailRequestSchema,
    genres: Iterable[GenreModel],
    actors: Iterable[ActorModel],
    languages: Iterable[LanguageModel],
    country: CountryModel,
) -> MovieModel:
    relation_fields = ("genres", "actors", "languages", "country")
    new_movie = MovieModel(**movie.model_dump(exclude=relation_fields))
    relation_objects = (genres, actors, languages, country)
    for field, objects in zip(relation_fields, relation_objects):
        setattr(
            new_movie, field, list(objects) if isinstance(objects, tuple) else objects
        )

    db.add(new_movie)
    return new_movie


async def get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel:
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
    )
    return await db.scalar(stmt)


@commit_decorator
async def delete_movie_by_id(db: AsyncSession, movie_id: int) -> Optional[MovieModel]:
    stmt = delete(MovieModel).where(MovieModel.id == movie_id).returning(MovieModel)
    deleted_movie = (await db.execute(stmt)).scalar_one_or_none()
    print(deleted_movie)
    return deleted_movie


@commit_decorator
async def update_movie_by_id(
    db: AsyncSession, movie_id: int, movie: MoviePatchSchema
) -> Optional[MovieModel]:
    model_dump = movie.model_dump(exclude_unset=True)
    if not model_dump:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    stmt = (
        update(MovieModel)
        .where(MovieModel.id == movie_id)
        .values(**model_dump)
        .returning(MovieModel)
    )
    return (await db.execute(stmt)).scalar_one_or_none()
