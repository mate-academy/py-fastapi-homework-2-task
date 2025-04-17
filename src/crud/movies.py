from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel
from database.models import CountryModel
from schemas.movies import CountryCreateSchema


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


async def check_if_movie_exist(
    db: AsyncSession,
    movie_name: str,
    movie_date: date
):
    query = select(MovieModel).where(
        and_(
            MovieModel.name == movie_name,
            MovieModel.date == movie_date
        )
    )
    result = await db.execute(query)
    movie = result.scalars().first()
    return movie


async def get_country(db: AsyncSession, county_code: str):
    query = select(CountryModel).where(CountryModel.code == county_code)
    result = await db.execute(query)
    country = result.scalar_one_or_none()
    return country


async def create_country(db: AsyncSession, country: CountryCreateSchema):
    new_country = CountryModel(**country.model_dump())
    db.add(new_country)
    await db.commit()
    await db.refresh(new_country)
    return new_country
