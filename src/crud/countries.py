from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CountryModel
from schemas.countries import CountryAddedSchema


async def get_country_by_params(params: dict, session: AsyncSession) -> CountryModel | None:
    """
    Fetch a country from the database using provided parameters.

    :param params: Dictionary of filter parameters (e.g., {"code": "USA"}).
    :param session: Async SQLAlchemy session.
    :return: CountryModel instance if found, otherwise None.
    """
    query = select(CountryModel).filter_by(**params)
    result = await session.execute(query)

    return result.scalar_one_or_none()


async def added_country(country_data: CountryAddedSchema, session: AsyncSession) -> CountryModel:
    """
    Add a new country to the database.

    :param country_data: Schema object containing the country data to be added.
    :param session: Async SQLAlchemy session.
    :return: The newly added CountryModel instance.
    """
    new_country = CountryModel(**country_data.model_dump())
    session.add(new_country)
    await session.commit()
    await session.refresh(new_country)

    return new_country
