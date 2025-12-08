from sqlalchemy import select


async def get_or_create_list(names: list[str], model, db):
    items = []
    for name in names:
        obj = select(model).where(model.name == name)
        obj = await db.scalar(obj)
        if obj is None:
            obj = model(name=name)
            db.add(obj)
        items.append(obj)

    return items