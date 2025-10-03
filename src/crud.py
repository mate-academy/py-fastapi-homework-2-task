from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models import MovieModel


async def get_movies(db: AsyncSession, per_page: int, page: int):
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return movies


async def get_or_create(model, db: AsyncSession, **kwargs):
    stmt = select(model).filter_by(**kwargs)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()
    if instance:
        return instance
    new_instance = model(**kwargs)
    db.add(new_instance)
    await db.flush()
    return new_instance


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.unique().scalar_one_or_none()


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    db_movie = result.unique().scalar_one_or_none()

    if not db_movie:
        return None

    await db.delete(db_movie)
    await db.commit()

    return db_movie
