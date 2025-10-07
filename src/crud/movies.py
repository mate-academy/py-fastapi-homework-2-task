from fastapi import Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    MovieModel,
)
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


async def get_movies(db: AsyncSession, per_page: int, page: int):
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel).offset(offset).limit(per_page).order_by(MovieModel.id.desc())
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return movies


async def get_or_create(model, db: AsyncSession, **kwargs):
    stmt = select(model).filter_by(**kwargs)
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()
    if instance:
        return instance
    new_instance = model(**kwargs)
    db.add(new_instance)
    await db.flush()
    return new_instance


async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    given = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    if given.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    genre = [await get_or_create(GenreModel, db, name=name) for name in movie.genres]
    actor = [await get_or_create(ActorModel, db, name=name) for name in movie.actors]
    language = [
        await get_or_create(LanguageModel, db, name=name) for name in movie.languages
    ]
    country = await get_or_create(
        CountryModel, db, code=movie.country, name=movie.country
    )

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
        genres=genre,
        actors=actor,
        languages=language,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    full_movie = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    return full_movie.unique().scalar_one()


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
    return result.unique().scalar_one_or_none()


async def delete_movie(db: AsyncSession, movie_id: int):
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
    db_movie = result.unique().scalar_one_or_none()

    if not db_movie:
        return None

    await db.delete(db_movie)
    await db.commit()

    return db_movie


async def update_movie(
    movie_id: int = Path(ge=1),
    update_data: MovieUpdateSchema = Body(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_dict = update_data.model_dump(exclude_unset=True)

    try:
        for field, value in update_dict.items():
            setattr(db_movie, field, value)
        await db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
