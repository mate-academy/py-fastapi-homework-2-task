from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models


async def get_or_create_country(db: AsyncSession, code: str):
    country = await db.scalar(
        select(models.CountryModel).where(models.CountryModel.code == code)
    )
    if country is None:
        country = models.CountryModel(code=code)
        db.add(country)
        await db.flush()
    return country
