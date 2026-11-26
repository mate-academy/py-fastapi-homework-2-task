from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LanguageModel
from schemas.languages import LanguageCreate


async def find_language_by_name(db: AsyncSession, name: str) -> LanguageModel | None:
    return await db.scalar(select(LanguageModel).where(LanguageModel.name == name))


async def create_language(
    db: AsyncSession, language_data: LanguageCreate
) -> LanguageModel:
    language = LanguageModel(**language_data.model_dump())
    db.add(language)

    await db.flush()

    return language


async def find_language_by_name_or_create(
    db: AsyncSession, language_data: LanguageCreate
) -> LanguageModel:
    language = await find_language_by_name(db, language_data.name)

    if language is None:
        language = await create_language(db=db, language_data=language_data)

    return language
