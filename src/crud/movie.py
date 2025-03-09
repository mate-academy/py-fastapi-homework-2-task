from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud.base import Base
from database import MovieModel
from schemas.movies import MovieUpdateSchema


class MovieDB(Base):
    model = MovieModel

    @classmethod
    async def get_movie_by_id(cls, db: AsyncSession, movie_id: int):
        query = (
            select(MovieModel)
            .options(
                joinedload(MovieModel.country),
                joinedload(MovieModel.genres),
                joinedload(MovieModel.actors),
                joinedload(MovieModel.languages),
            )
            .where(MovieModel.id == movie_id)
        )
        result = await db.execute(query)

        return result.scalars().first()

    @classmethod
    async def delete_movie_by_id(cls, db: AsyncSession, movie_id: int):
        movie_to_delete = await cls.get_movie_by_id(db, movie_id)
        if movie_to_delete:
            await db.delete(movie_to_delete)
            await db.commit()
            return
        raise ValueError("Movie with the given ID was not found.")

    @classmethod
    async def update_movie_by_id(
            cls,
            db: AsyncSession,
            movie_id: int,
            update_data: MovieUpdateSchema
    ):

        movie_to_update = await cls.find_one_or_none(db, id=movie_id)
        if not movie_to_update:
            raise ValueError("Movie with the given ID was not found.")
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(movie_to_update, key, value)

        await db.commit()
        await db.refresh(movie_to_update)
        return movie_to_update
