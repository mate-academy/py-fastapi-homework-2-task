from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel, GenreModel, ActorModel, LanguageModel


async def get_or_create_country(db: AsyncSession, country_code: str):
    result = await db.execute(select(CountryModel).where(CountryModel.code == country_code))
    country = result.scalar_one_or_none()
    if country:
        return country

    country = CountryModel(code=country_code, name=None)
    db.add(country)
    await db.commit()
    await db.refresh(country)
    return country


async def get_or_create_genres(db: AsyncSession, genre_names: List[str]):
    genres = []

    for name in genre_names:
        result = await db.execute(select(GenreModel).where(GenreModel.name == name))
        genre = result.scalar_one_or_none()
        if genre is None:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.commit()
            await db.refresh(genre)

        genres.append(genre)

    return genres


async def get_or_create_actors(db: AsyncSession, actor_names: List[str]):
    actors = []

    for name in actor_names:
        result = await db.execute(select(ActorModel).where(ActorModel.name == name))
        actor = result.scalar_one_or_none()
        if actor is None:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.commit()
            await db.refresh(actor)

        actors.append(actor)

    return actors


async def get_or_create_languages(db: AsyncSession, language_names: List[str]):
    languages = []

    for name in language_names:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == name))
        language = result.scalar_one_or_none()
        if language is None:
            language = LanguageModel(name=name)
            db.add(language)
            await db.commit()
            await db.refresh(language)

        languages.append(language)

    return languages
