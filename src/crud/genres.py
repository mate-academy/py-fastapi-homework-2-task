from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel
from schemas.genres import GenreCreate


async def find_genre_by_name(db: AsyncSession, name: str) -> GenreModel | None:
    return await db.scalar(select(GenreModel).where(GenreModel.name == name))


async def create_genre(db: AsyncSession, genre_data: GenreCreate) -> GenreModel:
    genre = GenreModel(**genre_data.model_dump())
    db.add(genre)

    await db.flush()

    return genre


async def find_genre_by_name_or_create(
    db: AsyncSession, genre_data: GenreCreate
) -> GenreModel:
    genre = await find_genre_by_name(db, genre_data.name)

    if genre is None:
        genre = await create_genre(db=db, genre_data=genre_data)

    return genre
