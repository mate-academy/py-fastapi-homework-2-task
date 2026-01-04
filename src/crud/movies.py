from datetime import datetime
from typing import Type
from fastapi import Depends, HTTPException
from pydantic import PositiveInt
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import (MovieModel,
                      get_db,
                      ActorModel,
                      GenreModel,
                      LanguageModel,
                      CountryModel)
from schemas import MovieCreate
from schemas.movies import MovieUpdateSchema


async def get_movie_by_name_and_date(db: AsyncSession, name: str, date: datetime.date) -> MovieModel:
    query = select(
        MovieModel
    ).where(
        (MovieModel.name.ilike(name)) & (MovieModel.date == date)
    )
    data = await db.execute(query)
    return data.scalar_one_or_none()


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


async def get_or_create_country(code: str, db: AsyncSession, country_came: str = None) -> CountryModel:
    stmt = select(CountryModel).where(CountryModel.code == code)
    result = await db.execute(stmt)
    country = result.scalars().first()

    if country:
        return country

    new_country = CountryModel(code=code, name=country_came)
    db.add(new_country)
    await db.flush()

    return new_country


async def get_all_movies(
        db: AsyncSession = Depends(get_db),
        page: int = 1,
        per_page: int = 10
) -> dict:

    offset = (page - 1) * per_page

    total_stmt = select(func.count()).select_from(MovieModel)
    result = await db.execute(total_stmt)
    total_items = result.scalar()

    stmt = select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    result = await db.execute(stmt)
    movies = result.scalars().all()

    total_pages = (total_items + per_page - 1) // per_page

    return {
        "movies": [] if movies is None else movies,
        "prev_page": f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "next_page": f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items
    }


async def get_movie_by_id(
        movie_id: PositiveInt,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


async def create_movie_model(db: AsyncSession, movie_data: MovieCreate) -> Type[MovieModel]:
    movie_data = movie_data.model_dump()
    country = movie_data.get("country")

    country = await get_or_create_country(db=db, code=country)
    genres = [await get_or_create(db=db, model=GenreModel, name=genre) for genre in movie_data.pop("genres")]
    actors = [await get_or_create(db=db, model=ActorModel, name=actor) for actor in movie_data.pop("actors")]
    languages = [await get_or_create(db=db, model=LanguageModel, name=language) for language in
                 movie_data.pop("languages")]

    movie = MovieModel(
        name=movie_data["name"],
        date=movie_data["date"],
        score=movie_data["score"],
        overview=movie_data["overview"],
        status=movie_data["status"],
        budget=movie_data["budget"],
        revenue=movie_data["revenue"],
        actors=actors,
        genres=genres,
        languages=languages,
        country=country,
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    movie = await get_movie_by_id(movie_id=movie.id, db=db)

    return movie


async def delete_movie_by_id(
        movie_id: PositiveInt,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


async def update_movie_by_id(
        movie_id: PositiveInt,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for var, value in update_data.items():
        if value is not None:
            setattr(movie, var, value)

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return movie
