from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db


async def db_async_params(db_async: AsyncSession = Depends(get_db)):
    return db_async

DbAsyncDep = Annotated[AsyncSession, Depends(db_async_params)]
