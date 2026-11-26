from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ActorModel
from schemas.actors import ActorCreate


async def find_actor_by_name(db: AsyncSession, name: str) -> ActorModel | None:
    return await db.scalar(select(ActorModel).where(ActorModel.name == name))


async def create_actor(db: AsyncSession, actor_data: ActorCreate) -> ActorModel:
    actor = ActorModel(**actor_data.model_dump())
    db.add(actor)

    await db.flush()

    return actor


async def find_actors_by_name_or_create(
    db: AsyncSession, actor_data: ActorCreate
) -> ActorModel:
    actor = await find_actor_by_name(db, actor_data.name)

    if actor is None:
        actor = await create_actor(db=db, actor_data=actor_data)

    return actor
