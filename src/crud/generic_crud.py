from typing import Type, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_or_create_entities(
        entity_data: list[str], model: Type, db: AsyncSession) -> List:

    if not entity_data:
        return []

    names = [name for name in entity_data]

    result = await db.execute(select(model).where(model.name.in_(names)))
    existing_entities = result.scalars().all()
    existing_map = {e.name: e for e in existing_entities}

    final_entities = []
    for name in entity_data:
        if name in existing_map:
            final_entities.append(existing_map[name])
        else:
            new_entity = model(name=name)
            db.add(new_entity)
            final_entities.append(new_entity)

    await db.flush()
    return final_entities
