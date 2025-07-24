from fastapi import Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def get_obj_count(db: AsyncSession):
    """Returns count of all movies"""
    stmt = select(func.count()).select_from(MovieModel)
    result = await db.execute(stmt)
    total_items = result.scalar_one()
    return total_items


async def get_movies(
    request: Request, db: AsyncSession, page: int = 1, per_page: int = 10
):
    stmt = (
        select(MovieModel)
        .offset((page - 1) * per_page)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .limit(per_page)
        .order_by(desc(MovieModel.id))
    )
    result = await db.execute(stmt)
    movies = result.scalars().unique().all()

    total_items = await get_obj_count(db)

    total_pages = (total_items + per_page - 1) // per_page
    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def name_data_unique_validaton(db: AsyncSession, movie_data: MovieCreateSchema):
    """Checks if there are two movies with the same name and date"""
    stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name, MovieModel.date == movie_data.date
    )

    result = await db.execute(stmt)
    existing_movie = result.scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )


async def get_or_create(db: AsyncSession, model, **kwargs):
    """Returns object or creates if not exist"""
    stmt = select(model).filter_by(**kwargs)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance

    else:
        instance = model(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance


async def create_film(db: AsyncSession, movie_data: MovieCreateSchema):
    await name_data_unique_validaton(db, movie_data)

    genres = [
        await get_or_create(db, GenreModel, name=genre_name)
        for genre_name in movie_data.genres
    ]
    actors = [
        await get_or_create(db, ActorModel, name=actor_name)
        for actor_name in movie_data.actors
    ]
    languages = [
        await get_or_create(db, LanguageModel, name=language_name)
        for language_name in movie_data.languages
    ]
    country = await get_or_create(db, CountryModel, code=movie_data.country)

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    movie_with_relations = result.scalars().first()

    return movie_with_relations


async def get_movie_with_id(movie_id: int, db: AsyncSession):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(db_movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdateSchema):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    data = movie.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)

    return db_movie
