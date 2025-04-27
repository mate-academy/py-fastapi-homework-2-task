from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_create(
    model, db: AsyncSession, value: str, field_name: str = "name"
):
    stmt = select(model).where(getattr(model, field_name) == value)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance
    instance = model(**{field_name: value})
    db.add(instance)
    await db.flush()
    return instance
