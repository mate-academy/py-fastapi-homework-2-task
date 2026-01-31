from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_create_entities(db: AsyncSession, model, names: list[str]):
    if not names:
        return []

    result = await db.execute(select(model).where(model.name.in_(names)))
    existing_entities = result.scalars().all()
    existing_names = {e.name for e in existing_entities}

    new_entities = [model(name=name) for name in names if
                    name not in existing_names]

    if new_entities:
        db.add_all(new_entities)

    return list(existing_entities) + new_entities
