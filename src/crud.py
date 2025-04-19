from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models import MovieModel
from src.schemas.movies import MovieCreate, MovieUpdate


async def get_films(db: AsyncSession):
    result = await db.execute(select(MovieModel))
    films = result.scalars().all()
    return films


async def get_film(db: AsyncSession, film_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == film_id))
    film = result.scalar_one_or_none()
    return film


async def create_film(db: AsyncSession, film: MovieCreate):
    new_film = MovieModel(**film.dict())
    db.add(new_film)
    await db.commit()
    await db.refresh(new_film)
    return new_film


async def delete_film(db: AsyncSession, film_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == film_id))
    db_film = result.scalar_one_or_none()
    if not db_film:
        return None
    await db.delete(db_film)
    await db.commit()
    return db_film


async def update_film(db: AsyncSession, film_id: int, film: MovieUpdate):
    result = await db.execute(select(MovieModel).where(MovieModel.id == film_id))
    db_film = result.scalar_one_or_none()
    if not db_film:
        return None

    db_film.name = film.name
    db_film.date = film.date
    db_film.score = film.score
    db_film.overview = film.overview
    db_film.status = film.status
    db_film.budget = film.budget
    db_film.revenue = film.revenue

    await db.commit()
    await db.refresh(db_film)
    return db_film
