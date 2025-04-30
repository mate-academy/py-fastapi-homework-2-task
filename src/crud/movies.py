from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.models import MovieModel
from schemas.movies import MovieCreate, MovieUpdate


async def create_movie(db: AsyncSession, movie: MovieCreate):
    new_movie = MovieModel(**movie.dict())
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


async def get_movie_by_id(db: AsyncSession, movie_id: int):
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
    movie = result.scalars().first()
    return movie


async def get_movies(db: AsyncSession):
    result = await db.execute(select(MovieModel))
    movies = result.scalars().all()
    return movies


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalars().first()
    if not db_movie:
        return None

    for key, value in movie.dict(exclude_unset=True).items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalars().first()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie
