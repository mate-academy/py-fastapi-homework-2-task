from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session_postgresql import get_postgresql_db

SessionDep = Annotated[AsyncSession, Depends(get_postgresql_db)]
