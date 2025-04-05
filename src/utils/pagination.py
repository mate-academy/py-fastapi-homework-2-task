from typing import Type, Any

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def get_total_items(db: AsyncSession, model: Type[Any]) -> int:
    total_stmt = select(func.count(model.id))
    result = await db.execute(total_stmt)
    return result.scalar() or 0


async def get_paginated_items(
        db: AsyncSession,
        model: Type[Any],
        offset: int,
        limit: int
) -> list:
    stmt = select(model).order_by(model.id.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


def get_pagination_links(
        page: int,
        per_page: int,
        total_pages: int
) -> tuple[str|None, str|None]:
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" \
        if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" \
        if page < total_pages else None
    return prev_page, next_page
