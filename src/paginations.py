from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlalchemy import (
    select,
    func
)

from schemas import (
    PaginationResponseSchema
)


async def get_paginated_query(query: Select, page: int, per_page: int) -> Select:
    offset = (page - 1) * per_page
    return query.offset(offset).limit(per_page)


async def get_paginated_response(
        query: Select,
        db: AsyncSession,
        page: int,
        per_page: int,
        url_path: str
) -> dict:
    """
    Returns dictionary in format:
    {
        "prev_page": "/theater/movies/?page=1&per_page=10",
        "next_page": "/theater/movies/?page=3&per_page=10",
        "total_pages": 1000,
        "total_items": 9999
    }
    :param query:
    :param db:
    :param per_page:
    :param page:
    :param url_path:
    :return:
    """
    total_items = await db.scalar(select(func.count()).select_from(query.subquery()))
    total_pages = total_items // per_page + (1 if total_items % per_page else 0)

    def get_page_url(page_num: int) -> str | None:
        if 1 <= page_num <= total_pages:
            return f"{url_path}?page={page_num}&per_page={per_page}"

    return PaginationResponseSchema(
        prev_page=get_page_url(page - 1),
        next_page=get_page_url(page + 1),
        total_pages=total_pages,
        total_items=total_items,
    ).model_dump()
