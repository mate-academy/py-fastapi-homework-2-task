from typing import Type
from database.models import Base, ActorModel, MovieModel
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from iso3166 import countries as iso

from schemas import (
    GenreCreateSchema,
    CountryCreateSchema,
    LanguageCreateSchema,
    ActorCreateSchema,
)
from database import (
    GenreModel,
    CountryModel,
    LanguageModel,
    ActorModel,
    MovieModel,
)


async def get_movie(session: AsyncSession, movie_id: int) -> MovieModel | None:
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_country(
    db: AsyncSession, country: CountryCreateSchema
) -> CountryModel:
    print("start creating country")
    new_country = CountryModel(**country.model_dump())
    db.add(new_country)
    await db.commit()
    await db.refresh(new_country)
    print(f"{new_country} created")
    return new_country


async def create_genre(
    db: AsyncSession, genre: GenreCreateSchema
) -> GenreModel:
    print("start creating genre")
    new_genre = GenreModel(**genre.model_dump())
    db.add(new_genre)
    await db.commit()
    await db.refresh(new_genre)
    print(f"{new_genre} created")
    return new_genre


async def create_actor(
    db: AsyncSession, actor: ActorCreateSchema
) -> ActorModel:
    print("start creating actor")
    new_actor = ActorModel(**actor.model_dump())
    db.add(new_actor)
    await db.commit()
    await db.refresh(new_actor)
    print(f"{new_actor} created")
    return new_actor


async def create_language(
    db: AsyncSession, language: LanguageCreateSchema
) -> LanguageModel:
    print("start creating language")
    new_language = LanguageModel(**language.model_dump())
    db.add(new_language)
    await db.commit()
    await db.refresh(new_language)
    print(f"{new_language} created")
    return new_language


# async def create_movie(
#     db: AsyncSession, movie: LanguageCreateSchema
# ) -> GenreModel:
#     country = iso.get(movie["country"])
#     movie["country"] = (country.name,)
#     new_movie = CountryModel(**movie.model_dump())
#
#     db.add(new_movie)
#     await db.commit()
#     await db.refresh(new_movie)
#     print(f"{new_movie} created")
#     return new_movie


# async def create_instance(
#     db: AsyncSession,
#     instance: BaseModel,
#     model: Type[Base],
# ) -> Base:
#     new_instance = model(**instance.model_dump())
#     db.add(new_instance)
#     await db.commit()
#     await db.refresh(new_instance)
#     return new_instance
