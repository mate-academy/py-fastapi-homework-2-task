from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LanguageModel
from schemas.languages import LanguageAddedSchema


async def get_language_by_params(params: dict, session: AsyncSession) -> LanguageModel | None:
    """
    Fetch a language from the database using provided parameters.

    :param params: Dictionary of filter parameters (e.g., {"name": "Ukrainian"}).
    :param session: Async SQLAlchemy session.
    :return: LanguageModel instance if found, otherwise None.
    """
    query = select(LanguageModel).filter_by(**params)
    result = await session.execute(query)

    return result.scalar_one_or_none()


async def added_language(language_data: LanguageAddedSchema, session: AsyncSession) -> LanguageModel:
    """
    Add a new language to the database.

    :param language_data: Schema object containing the language data to be added.
    :param session: Async SQLAlchemy session.
    :return: The newly added LanguageModel instance.
    """
    new_lang = LanguageModel(**language_data.model_dump())
    session.add(new_lang)
    await session.commit()
    await session.refresh(new_lang)

    return new_lang
