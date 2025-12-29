import datetime

from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import joinedload, selectinload
from sqlalchemy.sql.expression import select, desc
from sqlalchemy.sql.functions import func

import database
import schemas


async def get_or_create(db: AsyncSession, model, **kwargs):
    query = select(model).filter_by(**kwargs)
    result = await db.execute(query)
    instance = result.scalar_one_or_none()
    if instance:
        return instance
    instance = model(**kwargs)
    db.add(instance)
    await db.flush()
    return instance


async def get_all_movies(db: AsyncSession, start: int, count: int) -> Sequence[database.MovieModel]:
    query = select(database.MovieModel).offset(start).limit(count)
    query = query.order_by(desc(database.MovieModel.id))
    data = await db.execute(query)
    return data.scalars().all()


async def get_movies_count(db: AsyncSession) -> int:
    query = select(func.count(database.MovieModel.id))
    data = await db.execute(query)
    return data.scalar_one()


async def delete_movie_by_id(db: AsyncSession, movie_id: int) -> bool:
    movie = await db.get(database.MovieModel, movie_id)
    if not movie:
        return False
    await db.delete(movie)
    await db.commit()
    return True


async def get_movie_by_id_relations(db: AsyncSession, movie_id: int) -> database.MovieModel:
    query = select(database.MovieModel).where(database.MovieModel.id == movie_id)
    query = query.options(
        joinedload(database.MovieModel.country),
        selectinload(database.MovieModel.genres),
        selectinload(database.MovieModel.actors),
        selectinload(database.MovieModel.languages),
    )
    data = await db.execute(query)
    return data.scalar_one_or_none()


async def get_movie_by_name_and_date(db: AsyncSession, name: str, date: datetime.date) -> database.MovieModel:
    query = select(
        database.MovieModel
    ).where(
        (database.MovieModel.name.ilike(name)) & (database.MovieModel.date == date)
    )
    data = await db.execute(query)
    return data.scalar_one_or_none()


async def create_movie_model(db: AsyncSession, movie_data: schemas.MovieCreateSchema) -> database.MovieModel:
    movie_data = movie_data.model_dump()
    country = await get_or_create(db=db, model=database.CountryModel, code=movie_data.pop("country"))
    genres = [await get_or_create(db=db, model=database.GenreModel, name=genre) for genre in movie_data.pop("genres")]
    actors = [await get_or_create(db=db, model=database.ActorModel, name=actor) for actor in movie_data.pop("actors")]
    languages = [await get_or_create(db=db, model=database.LanguageModel, name=language) for language in
                 movie_data.pop("languages")]
    movie = database.MovieModel(
        **movie_data,
    )
    movie.country = country
    movie.genres = genres
    movie.actors = actors
    movie.languages = languages
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    movie = await get_movie_by_id_relations(db, movie_id=movie.id)
    return movie


async def update_movie_model(
        db: AsyncSession,
        movie_id: int,
        movie: schemas.MovieEditSchema) -> bool:
    instance = await db.get(database.MovieModel, movie_id)
    if not instance:
        return False
    data = movie.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(instance, key, value)
    await db.commit()
    await db.refresh(instance)
    return True
