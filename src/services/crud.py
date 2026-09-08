import datetime
from typing import Any, TypeVar

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    MovieModel,
)
from schemas.movies import MovieUpdateSchema


ModelType = TypeVar("ModelType")


async def fetch_movies_page(
    db: AsyncSession,
    page: int,
    per_page: int,
) -> list[MovieModel]:
    statement = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    result = await db.scalars(statement)

    return list(result.all())


async def count_movies(db: AsyncSession) -> int:
    statement = select(func.count()).select_from(MovieModel)
    total_items = await db.scalar(statement)

    return total_items or 0


async def movie_exists(
    db: AsyncSession,
    movie_name: str,
    movie_date: datetime.date,
) -> bool:
    statement = select(
        exists().where(
            MovieModel.name == movie_name,
            MovieModel.date == movie_date,
        )
    )

    return bool(await db.scalar(statement))


async def get_or_create_entity(
    db: AsyncSession,
    model: type[ModelType],
    defaults: dict[str, Any] | None = None,
    **lookup_fields: Any,
) -> tuple[ModelType, bool]:
    statement = select(model).filter_by(**lookup_fields)
    instance = await db.scalar(statement)

    if instance is not None:
        return instance, False

    values = {
        **lookup_fields,
        **(defaults or {}),
    }
    instance = model(**values)

    db.add(instance)
    await db.flush()

    return instance, True


async def get_or_create_named_entity(
    db: AsyncSession,
    model: type[ModelType],
    name: str,
) -> tuple[ModelType, bool]:
    cleaned_name = name.strip()

    statement = select(model).where(
        func.lower(model.name) == cleaned_name.lower()
    )
    instance = await db.scalar(statement)

    if instance is not None:
        return instance, False

    instance = model(name=cleaned_name)

    db.add(instance)
    await db.flush()

    return instance, True


async def get_or_create_named_entities(
    db: AsyncSession,
    model: type[ModelType],
    names: list[str],
) -> list[ModelType]:
    instances: list[ModelType] = []

    for name in names:
        instance, _ = await get_or_create_named_entity(
            db=db,
            model=model,
            name=name,
        )
        instances.append(instance)

    return instances


async def create_movie_record(
    db: AsyncSession,
    movie_data: dict[str, Any],
    country: CountryModel,
    genres: list[GenreModel],
    actors: list[ActorModel],
    languages: list[LanguageModel],
) -> MovieModel:
    movie = MovieModel(
        **movie_data,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return movie


async def get_movie_record_by_id(
    db: AsyncSession,
    movie_id: int,
) -> MovieModel | None:
    statement = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    return await db.scalar(statement)


async def delete_movie_record(
    db: AsyncSession,
    movie_id: int,
) -> MovieModel | None:
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if movie is None:
        return None

    await db.delete(movie)
    await db.commit()

    return movie


async def update_movie_record(
    db: AsyncSession,
    movie_id: int,
    movie_data: MovieUpdateSchema,
) -> MovieModel | None:
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if movie is None:
        return None

    update_data = movie_data.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        setattr(movie, field_name, value)

    await db.commit()
    await db.refresh(movie)

    return movie
