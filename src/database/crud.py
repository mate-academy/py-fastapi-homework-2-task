from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from schemas import MovieCreateSchema, MovieUpdateSchema
from .models import MovieModel, CountryModel, GenreModel, ActorModel, \
    LanguageModel


async def get_or_create_country(db: AsyncSession, code: str):
    result = await db.execute(
        select(CountryModel).where(CountryModel.code == code))
    country = result.scalar_one_or_none()
    if country:
        return country
    country = CountryModel(code=code)
    db.add(country)
    await db.flush()
    return country


async def get_or_create_items(db: AsyncSession, model, names: list[str]):
    items = []
    for name in names:
        result = await db.execute(select(model).where(model.name == name))
        item = result.scalar_one_or_none()
        if not item:
            item = model(name=name)
            db.add(item)
            await db.flush()
        items.append(item)
    return items


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    existing = await db.execute(select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country_result = await db.execute(select(CountryModel).where(
        CountryModel.code == movie.country))
    country = country_result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in movie.genres:
        genre_result = await db.execute(
            select(GenreModel).where(GenreModel.name == name))
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in movie.actors:
        actor_result = await db.execute(
            select(ActorModel).where(ActorModel.name == name))
        actor = actor_result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in movie.languages:
        lang_result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == name))
        lang = lang_result.scalar_one_or_none()
        if not lang:
            lang = LanguageModel(name=name)
            db.add(lang)
            await db.flush()
        languages.append(lang)

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
    return result.unique().scalar_one()


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )
    movie = result.unique().scalar_one_or_none()
    return movie


async def get_movies(db: AsyncSession):
    result = await db.execute(select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ))
    movies = result.unique().scalars().all()[::-1]
    return movies


async def update_movie_partial(db: AsyncSession, movie_id: int,
                               movie_update: MovieUpdateSchema):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    if movie_update.date is not None:
        if movie_update.date > date.today() + timedelta(days=365):
            raise HTTPException(status_code=400,
                                detail="Release date cannot be more than one year in the future.")

    update_data = movie_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()
    return


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie
