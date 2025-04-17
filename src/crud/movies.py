from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def get_movies(db: AsyncSession, page: int = 1, per_page: int = 10):
    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)
    total_items = count_result.scalar()

    if total_items == 0:
        return None

    offset = (page - 1) * per_page

    query = select(MovieModel).limit(per_page).offset(offset)
    result = await db.execute(query)
    movies = result.scalars().all()

    return movies, total_items
