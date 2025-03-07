from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import MovieModel
from schemas.movies import MovieCreate, MovieUpdate


async def create_movie(db: AsyncSession, movie: MovieCreate):
    new_movie = MovieModel(**movie.dict())
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie

async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    return movie

async def get_movies(db: AsyncSession):
    result = await db.execute(select(MovieModel))
    movies = result.scalars().all()
    return movies

async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    db_movie.title = movie.title
    db_movie.genre = movie.genre
    db_movie.price = movie.price
    await db.commit()
    await db.refresh(db_movie)
    return db_movie

async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie
