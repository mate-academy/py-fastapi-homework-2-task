from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base

ModelT = TypeVar("ModelT", bound=Base)


async def get_or_create(
    model: ModelT,
    db: AsyncSession,
    many=False,
    data=dict | list[dict],
) -> ModelT | list[ModelT]:
    data_: list[dict] = data if many else [data]
    instances: list[ModelT] = []

    for data_item in data_:
        filter_attrs = {}

        for attr in data_item.keys():
            filter_attrs[getattr(model, attr)] = data_item[attr]

        query = select(model)
        for filter_attr, attr_value in filter_attrs.items():
            query = query.filter(filter_attr == attr_value)

        query_result = await db.execute(query)
        instance = query_result.scalar_one_or_none()

        if not instance:
            instance = model(**data_item)
            db.add(instance)
            await db.commit()
            await db.refresh(instance)

        instances.append(instance)

    return instances if many else instances[0]
