from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ActorModel
from schemas.actors import ActorAddedSchema


async def get_actor_by_params(params: dict, session: AsyncSession) -> ActorModel | None:
    """
    Fetch a actor from the database using provided parameters.

    :param params: Dictionary of filter parameters (e.g., {"name": "John Wick"}).
    :param session: Async SQLAlchemy session.
    :return: ActorModel instance if found, otherwise None.
    """
    query = select(ActorModel).filter_by(**params)
    result = await session.execute(query)

    return result.scalar_one_or_none()


async def added_actor(actor_data: ActorAddedSchema, session: AsyncSession) -> ActorModel:
    """
    Add a new actor to the database.

    :param actor_data: Schema object containing the actor data to be added.
    :param session: Async SQLAlchemy session.
    :return: The newly added ActorModel instance.
    """
    new_actor = ActorModel(**actor_data.model_dump())
    session.add(new_actor)
    await session.commit()
    await session.refresh(new_actor)

    return new_actor
