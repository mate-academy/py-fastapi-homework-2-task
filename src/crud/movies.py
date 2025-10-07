from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieModel,
    MovieStatusEnum,
)
from schemas.movies import MovieUpdateSchema, MovieCreateSchema


async def get_or_create(
    db: AsyncSession, model, defaults: dict | None = None, **kwargs
):

    stmt = select(model).filter_by(**kwargs)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance

    params = {**kwargs, **(defaults or {})}
    new_instance = model(**params)
    db.add(new_instance)
    await db.flush()
    return new_instance


async def get_movie_by_id(movie_id: int, db: AsyncSession):
    query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    result = await db.execute(query)
    return result.scalars().first()


async def get_list_movies(db: AsyncSession, page: int, per_page: int):
    offset = (page - 1) * per_page
    res = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = res.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    count_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = count_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    return movies, total_items, total_pages


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    stmt = select(MovieModel).filter_by(name=movie.name, date=movie.date)
    result = await db.execute(stmt)
    existing_movie = result.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = await get_or_create(db, CountryModel, code=movie.country)
    genres = [await get_or_create(db, GenreModel, name=g) for g in movie.genres]
    actors = [await get_or_create(db, ActorModel, name=a) for a in movie.actors]
    languages = [
        await get_or_create(db, LanguageModel, name=lang) for lang in movie.languages
    ]

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    return result.scalars().first()


async def delete_movie(db: AsyncSession, movie_id: int):
    stmt = select(MovieModel).filter_by(id=movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    else:
        await db.delete(movie)
        await db.commit()


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdateSchema):
    stmt = select(MovieModel).filter_by(id=movie_id)
    result = await db.execute(stmt)
    existing_movie = result.scalar_one_or_none()

    if existing_movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update = movie.model_dump(exclude_unset=True)

    if "name" in update or "date" in update:
        new_name = update.get("name", existing_movie.name)
        new_date = update.get("date", existing_movie.date)

        stmt_check = select(MovieModel).filter(
            MovieModel.name == new_name,
            MovieModel.date == new_date,
            MovieModel.id != movie_id,
        )

        check_result = await db.execute(stmt_check)
        duplicate = check_result.scalar_one_or_none()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{new_name}' and release date '{new_date}' already exists.",
            )

    try:
        if "score" in update and not (0 <= update["score"] <= 100):
            raise ValueError
        if "budget" in update and update["budget"] < 0:
            raise ValueError
        if "revenue" in update and update["revenue"] < 0:
            raise ValueError
        if "status" in update:
            if not isinstance(update["status"], MovieStatusEnum):
                update["status"] = MovieStatusEnum(update["status"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update.items():
        setattr(existing_movie, key, value)

    await db.commit()
    await db.refresh(existing_movie)

    return {"detail": "Movie updated successfully."}
