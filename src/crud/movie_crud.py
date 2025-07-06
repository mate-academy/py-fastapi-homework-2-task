from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import CountryModel


async def get_or_create_country(name_or_code: str, db: AsyncSession):
    result = await db.execute(
        select(CountryModel).where(
            or_(
                CountryModel.code == name_or_code,
                CountryModel.name == name_or_code
             )
        )
    )
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=name_or_code)
        db.add(country)
        await db.commit()
        await db.refresh(country)
    return country


async def get_or_create_many(model, names: list[str], db: AsyncSession):
    instances = []
    for name in names:
        result = await db.execute(select(model).where(model.name == name))
        obj = result.scalar_one_or_none()
        if not obj:
            obj = model(name=name)
            db.add(obj)
            await db.flush()
        instances.append(obj)
    return instances
