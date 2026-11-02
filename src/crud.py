from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel, ActorModel, MovieModel, LanguageModel


async def get_or_create_genres(db: AsyncSession, names: list[str]) -> list[GenreModel]:
    result = await db.scalars(select(GenreModel).where(GenreModel.name.in_(names)))
    found = {g.name: g for g in result.all()}
    new_genres = [GenreModel(name=n) for n in names if n not in found]
    db.add_all(new_genres)
    await db.flush()
    return list(found.values()) + new_genres


async def get_or_create_actors(db: AsyncSession, names: list[str]) -> list[ActorModel]:
    result = await db.scalars(select(ActorModel).where(ActorModel.name.in_(names)))
    found = {g.name: g for g in result.all()}
    new_actors = [ActorModel(name=n) for n in names if n not in found]
    db.add_all(new_actors)
    await db.flush()
    return list(found.values()) + new_actors


async def get_or_create_languages(
    db: AsyncSession, names: list[str]
) -> list[LanguageModel]:
    result = await db.scalars(
        select(LanguageModel).where(LanguageModel.name.in_(names))
    )
    found = {g.name: g for g in result.all()}
    new_languages = [LanguageModel(name=n) for n in names if n not in found]
    db.add_all(new_languages)
    await db.flush()
    return list(found.values()) + new_languages
