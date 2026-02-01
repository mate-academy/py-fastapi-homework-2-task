from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select, func

from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    CountryModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieUpdateSchema
)
from .exceptions import MovieNotFoundException, MovieAlreadyExistsException


async def _get_or_create(db: AsyncSession, model, **kwargs):
    stmt = select(model)
    for key, value in kwargs.items():
        stmt = stmt.where(getattr(model, key) == value)

    result = await db.execute(stmt)
    instance = result.scalars().first()

    if instance:
        return instance

    instance = model(**kwargs)
    db.add(instance)
    await db.flush()
    return instance


async def get_movie_by_id(movie_id: int, db: AsyncSession) -> MovieModel:
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
    movie = result.scalars().first()
    if not movie:
        raise MovieNotFoundException(
            f"Movie with ID {movie_id} does not exist."
        )

    return movie


async def get_all_movies(db: AsyncSession) -> list[MovieModel]:
    result = await db.execute(
        select(MovieModel)
    )
    movies = result.scalars().all()
    return movies


async def get_movies_page(
    db: AsyncSession,
    offset: int,
    limit: int
) -> tuple[list[MovieModel], int]:
    total = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(limit)
    )

    movies = result.scalars().all()
    return movies, total


async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession
) -> MovieModel:
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.name == movie_data.name)
        .where(MovieModel.date == movie_data.date)
    )
    existing_movie = result.scalars().first()
    if existing_movie:
        raise MovieAlreadyExistsException(
            f"Movie '{movie_data.name}' on date '{movie_data.date}' already exists."
        )

    country = await _get_or_create(
        db,
        CountryModel,
        code=movie_data.country
    )

    genres = []
    for genre_name in movie_data.genres:
        genre = await _get_or_create(
            db,
            GenreModel,
            name=genre_name
        )
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = await _get_or_create(
            db,
            ActorModel,
            name=actor_name
        )
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = await _get_or_create(
            db,
            LanguageModel,
            name=language_name
        )
        languages.append(language)

    movie = MovieModel(
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
        languages=languages
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )

    result = await db.execute(stmt)
    return result.scalar_one()


async def update_movie(
    movie_id: int,
    movie_data: dict,
    db: AsyncSession
) -> MovieModel:
    movie = await get_movie_by_id(movie_id, db)

    related_models = {
        "country": CountryModel,
        "genres": GenreModel,
        "actors": ActorModel,
        "languages": LanguageModel,
    }

    for key, value in movie_data.items():
        if value is None:
            continue

        if key in related_models:
            model = related_models[key]

            if isinstance(value, list):
                related_objects = []
                for item in value:
                    obj = await _get_or_create(db, model, name=item)
                    related_objects.append(obj)
                setattr(movie, key, related_objects)
            else:
                obj = await _get_or_create(
                    db,
                    model,
                    code=value if key == "country" else None
                )
                setattr(movie, key, obj)
        else:
            setattr(movie, key, value)

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie


async def delete_movie(movie_id: int, db: AsyncSession) -> None:
    movie = await get_movie_by_id(movie_id, db)
    if not movie:
        raise MovieNotFoundException(
            f"Movie with ID {movie_id} does not exist."
        )

    await db.delete(movie)
    await db.commit()
