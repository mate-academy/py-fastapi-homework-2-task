from typing import Annotated

from fastapi import Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db


async def pagination_params(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
) -> dict:
    return {
        "page": page,
        "per_page": per_page,
    }

PaginationDep = Annotated[dict, Depends(pagination_params)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]
