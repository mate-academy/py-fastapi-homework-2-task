from typing import TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel, ActorModel, LanguageModel, MovieModel

ModelT = TypeVar("ModelT", MovieModel, GenreModel, ActorModel, LanguageModel)


async def count_items(db: AsyncSession, model: type[ModelT]):
    return await db.scalar(select(func.count(model.id)))


async def get_or_create_by_field(
    db: AsyncSession,
    model: type[ModelT],
    field: str,
    values: list[str],
) -> list[ModelT]:
    column = getattr(model, field)
    values = list(dict.fromkeys(values))
    existing = await db.scalars(select(model).where(column.in_(values)))
    by_value = {getattr(obj, field): obj for obj in existing}

    for value in values:
        if value not in by_value:
            obj = model(**{field: value})
            db.add(obj)
            by_value[value] = obj

    return [by_value[value] for value in values]
