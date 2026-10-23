from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from src.schemas.movies import MovieCreateSchema, MovieUpdateSchema


class DuplicateMovieError(Exception):
    pass


async def _get_or_create_related(
        db: AsyncSession, model, field_name: str, values: list[str]
):
    instances = []
    for val in values:
        stmt = select(model).where(getattr(model, field_name) == val)
        result = await db.execute(stmt)
        instance = result.scalars().first()
        if not instance:
            instance = model(**{field_name: val})
            db.add(instance)
            await db.flush()
        instances.append(instance)
    return instances


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    stmt_existing = select(MovieModel).where(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date,
    )
    result_existing = await db.execute(stmt_existing)
    if result_existing.scalars().first():
        raise DuplicateMovieError(
            f"A movie with the name '{movie.name}' and release date '{movie.date.isoformat()}' already exists."
        )

    country_stmt = select(CountryModel).where(
        (CountryModel.name == movie.country) | (CountryModel.code == movie.country)
    )
    res_country = await db.execute(country_stmt)
    country = res_country.scalars().first()
    if not country:
        country = CountryModel(name=movie.country, code=movie.country)
        db.add(country)
        await db.flush()

    genres = await _get_or_create_related(db, GenreModel, "name", movie.genres)
    actors = await _get_or_create_related(db, ActorModel, "name", movie.actors)
    languages = await _get_or_create_related(db, LanguageModel, "name", movie.languages)

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

    return await get_movie(db, new_movie.id)


async def get_movie(db: AsyncSession, movie_id: int):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_movies(db: AsyncSession):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            joinedload(MovieModel.country),
        )
        .order_by(MovieModel.id.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdateSchema):
    db_movie = await get_movie(db, movie_id)
    if not db_movie:
        return None

    update_data = movie.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field not in ("genres", "actors", "languages", "country"):
            setattr(db_movie, field, value)

    if "country" in update_data and update_data["country"] is not None:
        country_stmt = select(CountryModel).where(
            (CountryModel.name == update_data["country"]) | (CountryModel.code == update_data["country"])
        )
        res_country = await db.execute(country_stmt)
        country = res_country.scalars().first()
        if not country:
            country = CountryModel(
                name=update_data["country"],
                code=update_data["country"]
            )
            db.add(country)
            await db.flush()
        db_movie.country_id = country.id

    if "genres" in update_data and update_data["genres"] is not None:
        db_movie.genres = await _get_or_create_related(
            db,
            GenreModel,
            "name",
            update_data["genres"]
        )

    if "actors" in update_data and update_data["actors"] is not None:
        db_movie.actors = await _get_or_create_related(
            db,
            ActorModel,
            "name",
            update_data["actors"]
        )

    if "languages" in update_data and update_data["languages"] is not None:
        db_movie.languages = await _get_or_create_related(
            db,
            LanguageModel,
            "name",
            update_data["languages"]
        )

    await db.commit()
    return await get_movie(db, movie_id)


async def delete_movie(db: AsyncSession, movie_id: int):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    db_movie = result.scalars().first()
    if not db_movie:
        return None

    await db.delete(db_movie)
    await db.commit()
    return db_movie
