from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel
from schemas.countries import CountryCreateSchema


async def fetch_or_create_countries(country: str, db: AsyncSession) -> CountryModel:

    schema = CountryCreateSchema(code=country)

    result = await db.execute(
        select(CountryModel).where(CountryModel.code == schema.code)
    )

    existing_country = result.scalars().first()

    if existing_country:
        return existing_country

    country_model = CountryModel(code=schema.code)
    db.add(country_model)
    await db.flush()

    return country_model
