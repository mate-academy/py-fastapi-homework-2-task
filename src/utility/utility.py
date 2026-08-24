from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


async def create_country(
    db: DatabaseSession, country_name: str | None
) -> CountryModel | None:
    if not country_name:
        return None
    query = select(CountryModel).where(CountryModel.name == country_name)
    result = await db.execute(query)
    instance = result.scalar_one_or_none()

    if not instance:
        instance = CountryModel(name=country_name, code=country_name[:2].upper())
        db.add(instance)
        await db.flush()
    return instance


async def create_genres(
    db: DatabaseSession, genre_names: list[str]
) -> list[GenreModel]:
    instances = []
    for name in genre_names:
        query = select(GenreModel).where(GenreModel.name == name)
        result = await db.execute(query)
        instance = result.scalar_one_or_none()

        if not instance:
            instance = GenreModel(name=name)
            db.add(instance)
            await db.flush()
        instances.append(instance)
    return instances


async def create_actors(
    db: DatabaseSession, actor_names: list[str]
) -> list[ActorModel]:
    instances = []
    for name in actor_names:
        query = select(ActorModel).where(ActorModel.name == name)
        result = await db.execute(query)
        instance = result.scalar_one_or_none()

        if not instance:
            instance = ActorModel(name=name)
            db.add(instance)
            await db.flush()
        instances.append(instance)
    return instances


async def create_languages(
    db: DatabaseSession, language_names: list[str]
) -> list[LanguageModel]:
    instances = []
    for name in language_names:
        query = select(LanguageModel).where(LanguageModel.name == name)
        result = await db.execute(query)
        instance = result.scalar_one_or_none()

        if not instance:
            instance = LanguageModel(name=name)
            db.add(instance)
            await db.flush()
        instances.append(instance)
    return instances
