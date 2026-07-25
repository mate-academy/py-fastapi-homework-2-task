from typing import Sequence

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def get_all_movies(session: AsyncSession, page: int, per_page: int) -> tuple[Sequence[MovieModel], int]:
    offset = (page - 1) * per_page

    count_stmt = select(func.count(MovieModel.id))
    total_items = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    movies = result.scalars().all()

    return movies, total_items
