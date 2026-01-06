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

    country = models.CountryModel(code=code, name=None)
    db.add(country)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        country = await db.scalar(stmt)
        if not country:
            raise
    return country


async def get_or_create_by_name(db, Model, names: list[str]):
    if not names:
        return []

    stmt = select(Model).where(Model.name.in_(names))
    existing = (await db.scalars(stmt)).all()
    existing_by_name = {x.name: x for x in existing}

    created = []
    for name in names:
        if name in existing_by_name:
            continue
        obj = Model(name=name)
        db.add(obj)
        created.append(obj)

    if created:
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            existing = (await db.scalars(stmt)).all()
            existing_by_name = {x.name: x for x in existing}
            created = [existing_by_name[n] for n in names if n in existing_by_name]

    return [existing_by_name.get(n) or next(x for x in created if x.name == n) for n in names]

