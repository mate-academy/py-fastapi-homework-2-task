from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def get_movies(db: AsyncSession, per_page: int, page: int) -> Sequence[MovieModel]:
    movies = await db.execute(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    return movies.scalars().all()


async def get_number_of_movies(db: AsyncSession) -> int:
    return (await db.execute(select(func.count()).select_from(MovieModel))).scalar()
