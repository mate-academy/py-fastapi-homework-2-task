from typing import Sequence, Any

from sqlalchemy import delete, select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud.actors import get_actor_by_params, added_actor
from crud.countries import added_country, get_country_by_params
from crud.genres import get_genre_by_params, added_genre
from crud.languages import get_language_by_params, added_language
from database import MovieModel
from schemas.actors import ActorAddedSchema
from schemas.countries import CountryAddedSchema
from schemas.genres import GenreAddedSchema
from schemas.languages import LanguageAddedSchema
from schemas.movies import MovieAddedSchema, MovieUpdateSchema


async def get_count_movies(session: AsyncSession) -> int:
    """
    Returns the total number of movies in the database.

    :param session: Async SQLAlchemy session.
    :return: Integer count of movie records.
    """
    return await session.scalar(select(func.count()).select_from(MovieModel))


async def fetch_movies(
        session: AsyncSession,
        offset: int | None = None,
        limit: int | None = None
) -> Sequence[MovieModel] | None:
    """
    Fetch a list of movies from the database with optional pagination.

    :param session: Async SQLAlchemy session.
    :param offset: Number of records to skip (used for pagination).
    :param limit: Maximum number of records to return.
    :return: A sequence of MovieModel instances or None if no movies found.
    """
    stmt = select(MovieModel).order_by(MovieModel.id.desc())

    if offset:
        stmt = stmt.offset(offset)
    if limit:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    movies = result.unique().scalars().all()

    return movies


async def fetch_movie_by_id(movie_id: int, session: AsyncSession) -> MovieModel | None:
    """
    Fetch a single movie by its ID, including related country, genres, actors, and languages.

    :param movie_id: ID of the movie to retrieve.
    :param session: Async SQLAlchemy session.
    :return: MovieModel instance if found, otherwise None.
    """
    stmt = select(MovieModel).where(MovieModel.id == movie_id).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
    )
    result = await session.execute(stmt)

    return result.unique().scalar_one_or_none()


async def fetch_movie_by_params(params: dict[str, Any], session: AsyncSession) -> MovieModel | None:
    """
    Fetch a single movie based on dynamic filter parameters.

    :param params: Dictionary of field-value pairs to filter the movie.
    :param session: Async SQLAlchemy session.
    :return: MovieModel instance if found, otherwise None.
    """
    stmt = select(MovieModel).filter_by(**params)
    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def added_movie(movie_schema: MovieAddedSchema, session: AsyncSession) -> MovieModel | dict[str, str]:
    """
    Add a new movie with related entities (country, genres, actors, languages).

    If related entities (by name/code) are not found, they are created.

    :param movie_schema: Schema containing movie data and related entity names.
    :param session: Async SQLAlchemy session.
    :return: The created MovieModel instance, or a dict with an error message on failure.
    """
    movie_data = movie_schema.model_dump()

    country_code = movie_data.pop("country", "")
    genre_names = movie_data.pop("genres", [])
    actor_names = movie_data.pop("actors", [])
    language_names = movie_data.pop("languages", [])

    genres = []
    actors = []
    languages = []

    country = await get_country_by_params(
        {"code": country_code},
        session=session,
    )

    if country is None:
        country = await added_country(CountryAddedSchema(code=country_code), session=session)

    for genre_name in genre_names:
        genre = await get_genre_by_params({"name": genre_name}, session=session)

        if genre is None:
            genre = await added_genre(GenreAddedSchema(name=genre_name), session=session)

        genres.append(genre)

    for actor_name in actor_names:
        actor = await get_actor_by_params({"name": actor_name}, session=session)

        if actor is None:
            actor = await added_actor(ActorAddedSchema(name=actor_name), session=session)

        actors.append(actor)

    for language_name in language_names:
        language = await get_language_by_params({"name": language_name}, session=session)

        if language is None:
            language = await added_language(LanguageAddedSchema(name=language_name), session=session)

        languages.append(language)

    new_movie = MovieModel(**movie_data)

    new_movie.country = country
    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages

    session.add(new_movie)

    try:
        await session.commit()
        await session.refresh(new_movie)

        return await fetch_movie_by_id(movie_id=new_movie.id, session=session)
    except IntegrityError:
        await session.rollback()

        return {"detail": "Invalid input data."}


async def edit_movie(movie_id: int, movie_schema: MovieUpdateSchema, session: AsyncSession) -> dict[str, str]:
    """
    Update an existing movie record with the given fields.

    Only the fields explicitly set in the update schema will be modified.

    :param movie_id: ID of the movie to update.
    :param movie_schema: Schema containing the fields to update.
    :param session: Async SQLAlchemy session.
    :return: A message indicating success or failure.
    """
    movie_data = movie_schema.model_dump(exclude_unset=True)
    stmt = update(MovieModel).where(MovieModel.id == movie_id).values(**movie_data)

    try:
        await session.execute(stmt)
        await session.commit()

        return {"detail": "Movie updated successfully."}

    except IntegrityError:

        await session.rollback()

        return {"detail": "Invalid input data."}


async def remove_movie(movie_id: int, session: AsyncSession) -> None:
    """
    Delete a movie from the database by its ID.

    :param movie_id: ID of the movie to delete.
    :param session: Async SQLAlchemy session.
    :return: None
    """
    stmt = delete(MovieModel).where(MovieModel.id == movie_id)

    await session.execute(stmt)
    await session.commit()
