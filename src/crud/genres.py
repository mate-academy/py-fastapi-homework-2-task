from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel
from schemas.genres import GenreAddedSchema


async def get_genre_by_params(params: dict, session: AsyncSession) -> GenreModel | None:
    """
    Fetch a genre from the database using provided parameters.

    :param params: Dictionary of filter parameters (e.g., {"name": "Drama"}).
    :param session: Async SQLAlchemy session.
    :return: GenreModel instance if found, otherwise None.
    """
    query = select(GenreModel).filter_by(**params)
    result = await session.execute(query)

    return result.scalar_one_or_none()


async def added_genre(genre_data: GenreAddedSchema, session: AsyncSession) -> GenreModel:
    """
    Add a new genre to the database.

    :param genre_data: Schema object containing the genre data to be added.
    :param session: Async SQLAlchemy session.
    :return: The newly added GenreModel instance.
    """
    new_genre = GenreModel(**genre_data.model_dump())
    session.add(new_genre)
    await session.commit()
    await session.refresh(new_genre)

    return new_genre
