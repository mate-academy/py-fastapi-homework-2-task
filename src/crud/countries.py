from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel
from schemas.countries import CountryCreate


async def find_country_by_code(db: AsyncSession, code: str) -> CountryModel | None:
    return await db.scalar(select(CountryModel).where(CountryModel.code == code))


async def create_country(db: AsyncSession, country_data: CountryCreate) -> CountryModel:
    country = CountryModel(**country_data.model_dump())
    db.add(country)

    await db.flush()

    return country


async def find_country_by_code_or_create(
    db: AsyncSession, country_data: CountryCreate
) -> CountryModel:
    country = await find_country_by_code(db, country_data.code)

    if country is None:
        country = await create_country(db=db, country_data=country_data)

    return country
