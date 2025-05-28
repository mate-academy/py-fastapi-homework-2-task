from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieCreateSchema
from schemas.movies import MovieUpdateSchema
from utils.db import get_or_create


async def get_movies(db: AsyncSession, page: int, per_page: int):
    movies_count_query = select(func.count(MovieModel.id))
    movies_count_result = await db.execute(movies_count_query)
    movies_count = movies_count_result.scalar_one()

    movies_query = (
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    movies_query_result = await db.execute(movies_query)
    movies = movies_query_result.scalars().all()

    return movies, movies_count


async def get_movie_by_id(db: AsyncSession, id: int):
    movie_query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .filter_by(id=id)
    )
    movie_query_result = await db.execute(movie_query)
    movie = movie_query_result.scalar_one_or_none()
    return movie


async def update_movie_relations(
    db: AsyncSession,
    movie: MovieModel,
    country: str,
    genres: list[str],
    actors: list[str],
    languages: list[str],
):
    movie.country = await get_or_create(
        CountryModel,
        db,
        data={"code": country},
    )

    movie.genres = await get_or_create(
        GenreModel,
        db,
        many=True,
        data=[{"name": genre_name} for genre_name in genres],
    )

    movie.actors = await get_or_create(
        ActorModel,
        db,
        many=True,
        data=[{"name": actor_name.strip()} for actor_name in actors],
    )

    movie.languages = await get_or_create(
        LanguageModel,
        db,
        many=True,
        data=[{"name": language_name} for language_name in languages],
    )

    return movie


async def create_movie(db: AsyncSession, movie_data: MovieCreateSchema):
    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
    )

    await update_movie_relations(
        db,
        movie,
        country=movie_data.country,
        genres=movie_data.genres,
        actors=movie_data.actors,
        languages=movie_data.languages,
    )

    db.add(movie)
    await db.commit()
    return await get_movie_by_id(db, movie.id)


async def delete_movie(db: AsyncSession, movie_id: int):
    delete_movie_query = delete(MovieModel).where(MovieModel.id == movie_id)
    delete_movie_result = await db.execute(delete_movie_query)

    movies_deleted = delete_movie_result.rowcount

    if movies_deleted:
        await db.commit()

    return movies_deleted


async def update_movie(
    db: AsyncSession,
    movie_id: int,
    movie_data: MovieUpdateSchema,
):
    update_data = movie_data.model_dump(exclude_unset=True)
    update_movie_query = (
        update(MovieModel)
        .values(**update_data)
        .where(MovieModel.id == movie_id)
    )
    update_movie_result = await db.execute(update_movie_query)

    movies_updated = update_movie_result.rowcount

    if movies_updated:
        await db.commit()

    return movies_updated
