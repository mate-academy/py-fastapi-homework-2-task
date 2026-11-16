import math
from fastapi import Request

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    db: AsyncSession,
    model: type(DeclarativeBase),
    request: Request,
    page: int,
    per_page: int
):
    count = select(func.count()).select_from(model)
    offset = (page - 1) * per_page

    total_items = await db.scalar(count)

    db_selection = (
        select(model)
        .offset(offset)
        .limit(per_page)
    )

    query = await db.execute(db_selection)

    items = query.scalars().all()
    total_pages = math.ceil(total_items / per_page)

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = str(request.url.include_query_params(page=page - 1, per_page=per_page))

    if page < total_pages:
        next_page = str(request.url.include_query_params(page=page + 1, per_page=per_page))

    return items, total_items, total_pages, prev_page, next_page
