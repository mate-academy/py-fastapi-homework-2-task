from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas import MovieCreateSchema, MovieUpdateSchema


async def get_movie_items_count(db: AsyncSession):
    return await db.scalar(select(func.count()).select_from(MovieModel))


async def get_movie_list(db: AsyncSession, offset: int, per_page: int = 10):
    stmt = await db.scalars(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    return stmt.all()


async def get_or_create_country_by_code(db: AsyncSession, country_code: str):
    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    if country is None:
        country = CountryModel(code=country_code)
        db.add(country)
        await db.flush()
    return country


async def get_or_create_genre(db: AsyncSession, genre_name: str):
    genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))
    if genre is None:
        genre = GenreModel(name=genre_name)
        db.add(genre)
        await db.flush()
    return genre


async def get_or_create_actor(db: AsyncSession, actor_name: str):
    actor = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))
    if actor is None:
        actor = ActorModel(name=actor_name)
        db.add(actor)
        await db.flush()
    return actor


async def get_or_create_language(db: AsyncSession, language_name: str):
    language = await db.scalar(
        select(LanguageModel).where(LanguageModel.name == language_name)
    )
    if language is None:
        language = LanguageModel(name=language_name)
        db.add(language)
        await db.flush()
    return language


async def name_and_date_is_unique(db: AsyncSession, movie: MovieCreateSchema):
    movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name and MovieModel.date == movie.date
        )
    )
    if movie is None:
        return True
    return False


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    if not await name_and_date_is_unique(db=db, movie=movie):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie.name}' and release date "
                f"'{movie.date}' already exists."
            ),
        )

    country = await get_or_create_country_by_code(db=db, country_code=movie.country)

    genres = [await get_or_create_genre(db, genre_name) for genre_name in movie.genres]

    actors = [await get_or_create_actor(db, actor_name) for actor_name in movie.actors]

    languages = [
        await get_or_create_language(db, language_name)
        for language_name in movie.languages
    ]

    movie_db = MovieModel(
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

    db.add(movie_db)

    await db.commit()
    await db.rollback()

    return movie_db


async def get_movie_by_id(db: AsyncSession, movie_id: int):
    return await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )


async def delete_movie_by_id(db: AsyncSession, movie_id: int):
    movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    if movie is None:
        return False
    await db.delete(movie)
    await db.commit()
    return True


async def update_movie(
    db: AsyncSession, movie_id: int, movie_payload: MovieUpdateSchema
):
    if (
        movie_payload.name
        and movie_payload.date
        and not await name_and_date_is_unique(db=db, movie=movie_payload)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_payload.name}' and release date "
                f"'{movie_payload.date}' already exists."
            ),
        )
    movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields were provided for update.",
        )

    score = update_data.get("score")
    budget = update_data.get("budget")
    revenue = update_data.get("revenue")

    if score is not None and not 0 <= score <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    if budget is not None and budget < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    if revenue is not None and revenue < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()
    await db.rollback()
