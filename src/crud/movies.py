import math

from fastapi import Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.country import create_country
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieDetailSchema, MovieCreateSchema
from schemas.movies import MovieUpdateSchema
from utills.get_or_create import get_or_create


async def get_all_movies(
        db: AsyncSession,
        page: int,
        per_page: int,
) -> dict:
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = math.ceil(total_items / per_page)

    skip = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(-MovieModel.id)
        .offset(skip)
        .limit(per_page)
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    movies_data = [MovieDetailSchema.model_validate(movie).dict() for movie in movies]

    return {
        "movies": movies_data,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


async def get_movie_by_id(
        film_id: int,
        db: AsyncSession
):
    result = await db.execute(select(
        MovieModel
    ).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ).where(MovieModel.id == film_id))
    film = result.scalar_one_or_none()
    if not film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return film


async def create_movie(film: MovieCreateSchema, db: AsyncSession):
    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == film.name,
            MovieModel.date == film.date
        )
    )
    if existing_movie.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{film.name}' "
                   f"and release date '{film.date}' already exists."
        )

    result = await db.execute(
        select(CountryModel).filter(CountryModel.code == film.country)
    )
    country = result.scalars().first()
    if not country:
        country = await create_country(film.country, db=db)

    genres = [
        await get_or_create(GenreModel, db=db, value=name) for name in film.genres
    ]

    actors = [
        await get_or_create(ActorModel, db=db, value=name) for name in film.actors
    ]

    languages = [
        await get_or_create(LanguageModel, db=db, value=name) for name in film.languages
    ]

    movie = MovieModel(
        name=film.name,
        date=film.date,
        score=film.score,
        overview=film.overview,
        status=film.status.value,
        budget=film.budget,
        revenue=film.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
        .where(MovieModel.id == movie.id)
    )
    return result.scalar_one()


async def delete_movie_by_id(film_id: int, db: AsyncSession):
    result = await db.execute(select(MovieModel).where(MovieModel.id == film_id))
    existing_movie = result.scalar_one_or_none()

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(existing_movie)
    await db.commit()


async def update_movie_by_id(
        film_id: int,
        film: MovieUpdateSchema,
        db: AsyncSession
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == film_id))
    existing_movie = result.scalar_one_or_none()

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")



    await db.commit()
    return {"detail": "Movie updated successfully."}
