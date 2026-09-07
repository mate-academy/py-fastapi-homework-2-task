from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel, MovieModel


ModelType = TypeVar("ModelType")


async def get_or_create_related(
    db: AsyncSession,
    model: type[ModelType],
    name: str,
) -> ModelType:
    result = await db.execute(
        select(model).where(model.name == name)
    )

    instance = result.scalar_one_or_none()

    if instance is None:
        instance = model(name=name)
        db.add(instance)
        await db.flush()

    return instance


async def get_or_create_country(
    db: AsyncSession,
    country_code: str,
) -> CountryModel:
    country_result = await db.execute(
        select(CountryModel)
        .where(CountryModel.code == country_code)
    )
    country = country_result.scalar_one_or_none()
    if country is None:
        country = CountryModel(code=country_code)
        db.add(country)
        await db.flush()

    return country
