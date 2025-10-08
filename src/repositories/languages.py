from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LanguageModel


class LanguageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(self, name: str, *, commit: bool = True) -> LanguageModel:
        language = await self.db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if language:
            return language

        language = LanguageModel(name=name)
        self.db.add(language)
        if commit:
            await self.db.commit()
            await self.db.refresh(language)
        return language
