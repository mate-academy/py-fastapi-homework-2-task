from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ActorModel


class ActorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create(self, name: str) -> ActorModel:
        actor = await self.db.scalar(select(ActorModel).where(ActorModel.name == name))
        if actor:
            return actor

        actor = ActorModel(name=name)
        self.db.add(actor)
        await self.db.commit()
        await self.db.refresh(actor)
        return actor
