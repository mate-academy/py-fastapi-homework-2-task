from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)


async def get_or_create_entities(db: AsyncSession, model, names: list[str], code_field: str = None):
    if not names:
        return []

    if code_field and len(names) == 1:
        existing = (await db.execute(
            select(model).where(getattr(model, code_field) == names[0])
        )).scalar_one_or_none()
        if existing:
            return [existing]
        new_entity = model(**{code_field: names[0], "name": names[0]})
        db.add(new_entity)
        await db.flush()
        return [new_entity]

    existing = (await db.execute(
        select(model).where(model.name.in_(names))
    )).scalars().all()

    existing_names = {e.name for e in existing}
    missing_names = set(names) - existing_names

    new_entities = [model(name=name) for name in missing_names]
    if new_entities:
        db.add_all(new_entities)
        await db.flush()

    return existing + new_entities


async def resolve_movie_relations(data: dict, db: AsyncSession):
    relations = {}

    if "country" in data:
        country_list = [data["country"]]
        countries = await get_or_create_entities(db, CountryModel, country_list, code_field="code")
        if not countries:
            raise HTTPException(status_code=400, detail="Invalid country code")
        relations["country"] = countries[0]

    if "genres" in data:
        relations["genres"] = await get_or_create_entities(db, GenreModel, data["genres"])

    if "actors" in data:
        relations["actors"] = await get_or_create_entities(db, ActorModel, data["actors"])

    if "languages" in data:
        relations["languages"] = await get_or_create_entities(db, LanguageModel, data["languages"])

    return relations
