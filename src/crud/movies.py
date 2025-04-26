from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import MovieModel
from schemas.movies import MovieCreate


async def create_film(db: AsyncSession, movie: MovieCreate):
    new_movie = MovieModel(**movie.dict())
    db.add(new_movie)
    await db.commit()
    await db.refresh()
    return new_movie
