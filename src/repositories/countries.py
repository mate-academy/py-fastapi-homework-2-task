from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel


class CountryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(self, code: str) -> CountryModel:
        country = await self.db.scalar(
            select(CountryModel).where(CountryModel.code == code)
        )
        if country:
            return country
        country = CountryModel(code=code)
        self.db.add(country)
        await self.db.commit()
        await self.db.refresh(country)
        return country
