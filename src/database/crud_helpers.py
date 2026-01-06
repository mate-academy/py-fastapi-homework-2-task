from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.database import models
from src.schemas.movies import MovieCreationRequestSchema


def unique_clean(items: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for x in items:
        x = x.strip()
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


async def get_or_create_country(db, code: str) -> models.CountryModel:
    stmt = select(models.CountryModel).where(models.CountryModel.code == code)
    country = await db.scalar(stmt)
    if country:
        return country

    try:
        async with db.begin_nested():
            country = models.CountryModel(code=code, name=None)
            db.add(country)
            await db.flush()
            return country
    except IntegrityError:
        country = await db.scalar(stmt)
        if not country:
            raise
        return country


async def get_or_create_by_name(db, Model, names: list[str]):
    if not names:
        return []

    names = unique_clean(names)

    # load existing first (1 query)
    stmt = select(Model).where(Model.name.in_(names))
    existing = (await db.scalars(stmt)).all()
    by_name = {obj.name: obj for obj in existing}

    # create missing one-by-one safely
    for name in names:
        if name in by_name:
            continue

        try:
            async with db.begin_nested():
                obj = Model(name=name)
                db.add(obj)
                await db.flush()
                by_name[name] = obj
        except IntegrityError:
            obj = await db.scalar(select(Model).where(Model.name == name))
            if obj is None:
                raise
            by_name[name] = obj

    return [by_name[n] for n in names]
