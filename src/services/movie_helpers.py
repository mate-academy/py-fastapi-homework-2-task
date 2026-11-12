from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import CountryModel


async def get_or_create_country(db: AsyncSession, code: str) -> CountryModel:
    stmt = select(CountryModel).where(CountryModel.code == code)
    result = await db.execute(stmt)
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=code, name=code)
        db.add(country)
        await db.flush()
    return country


async def get_or_create_entities(db: AsyncSession, model_class, names: list[str]):
    if not names:
        return []

    stmt = select(model_class).where(model_class.name.in_(names))
    result = await db.execute(stmt)
    existing_entities = {entity.name: entity for entity in result.scalars().all()}

    entities = []
    for name in names:
        if name in existing_entities:
            entities.append(existing_entities[name])
        else:
            new_entity = model_class(name=name)
            db.add(new_entity)
            await db.flush()
            entities.append(new_entity)

    return entities
