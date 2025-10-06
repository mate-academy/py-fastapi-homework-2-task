from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import GenreModel


class GenreRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(self, name: str) -> GenreModel:
        genre = await self.db.scalar(select(GenreModel).where(GenreModel.name == name))
        if genre:
            return genre

        genre = GenreModel(name=name)
        self.db.add(genre)
        await self.db.commit()
        await self.db.refresh(genre)
        return genre
