import pycountry
from asgiref.sync import sync_to_async
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel


@sync_to_async
def get_country_name_by_code(country_code: str) -> str | None:
    country = pycountry.countries.get(alpha_3=country_code.upper())
    return country.name if country else None


async def create_country(country_code: str, db: AsyncSession):
    country_name = await get_country_name_by_code(country_code)
    if not country_name:
        raise HTTPException(status_code=400, detail="Incorrect country code")
    country = CountryModel(code=country_code, name=country_name)
    db.add(country)
    await db.flush()
    return country
