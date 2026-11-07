import asyncio

from fastapi import Request, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

from database.models import CountryModel, MovieModel, GenreModel, ActorModel, LanguageModel
from config.settings import api_version_prefix
from schemas import MovieListResponseSchema
from schemas.movies import MovieListItemSchema, MovieCreateSchema, MovieUpdateSchema


async def get_or_create_country(country_code: str, db: AsyncSession, country_name: str = None) -> CountryModel:
    stmt = select(CountryModel).where(CountryModel.code == country_code)
    result = await db.execute(stmt)
    country_db = result.scalar_one_or_none()

    if not country_db:
        country_db = CountryModel(code=country_code, name=country_name)
        db.add(country_db)
    return country_db


async def get_or_create_genre(genre_name: str, db: AsyncSession) -> GenreModel:
    stmt = select(GenreModel).where(GenreModel.name == genre_name)
    result = await db.execute(stmt)
    genre_db = result.scalar_one_or_none()

    if not genre_db:
        genre_db = GenreModel(name=genre_name)
        db.add(genre_db)
    return genre_db


async def get_or_create_actor(actor_name: str, db: AsyncSession) -> ActorModel:
    stmt = select(ActorModel).where(ActorModel.name == actor_name)
    result = await db.execute(stmt)
    actor_db = result.scalar_one_or_none()
    if not actor_db:
        actor_db = ActorModel(name=actor_name)
        db.add(actor_db)
    return actor_db


async def get_or_create_language(language_name: str, db: AsyncSession) -> LanguageModel:
    stmt = select(LanguageModel).where(LanguageModel.name == language_name)
    result = await db.execute(stmt)
    language_db = result.scalar_one_or_none()
    if not language_db:
        language_db = LanguageModel(name=language_name)
        db.add(language_db)
    return language_db


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    country_task = get_or_create_country(movie.country, db)
    genres_task = asyncio.gather(
        *[get_or_create_genre(genre_name=genre_name, db=db) for genre_name in movie.genres]
    )
    actors_task = asyncio.gather(
        *[get_or_create_actor(actor_name=actor_name, db=db) for actor_name in movie.actors]
    )
    languages_task = asyncio.gather(
        *[get_or_create_language(language_name=language_name, db=db) for language_name in movie.languages]
    )

    country, genres, actors, languages = await asyncio.gather(
        country_task, genres_task, actors_task, languages_task
    )

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
        languages=languages
    )

    try:
        db.add(new_movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{new_movie.name}' and release date '{new_movie.date}' already exists."
        )

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    new_movie_with_relations = result.unique().scalar_one()

    return new_movie_with_relations


async def get_movie_by_id(db: AsyncSession, movie_id: int):
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
    db_movie = result.unique().scalar_one_or_none()
    return db_movie


async def get_movies(
        request: Request,
        page: int,
        per_page: int,
        db: AsyncSession
):

    offset = (page - 1) * per_page

    total_items_query = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_query.scalar()

    total_pages = (total_items + per_page - 1) // per_page

    if not total_items or page > total_pages:
        return None

    result = await db.execute(select(MovieModel).offset(offset).limit(per_page).order_by(MovieModel.id.desc()))
    movies = result.scalars().all()
    movie_schemas = [MovieListItemSchema.model_validate(movie) for movie in movies]

    full_path = request.url.path

    if full_path.startswith(api_version_prefix):
        base_url = full_path[len(api_version_prefix):]
    else:
        base_url = full_path

    query_template = f"?page={{}}&per_page={per_page}"
    prev_page = f"{base_url}{query_template.format(page - 1)}" if page > 1 else None
    next_page = f"{base_url}{query_template.format(page + 1)}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movie_schemas,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


async def edit_movie(db: AsyncSession, db_movie: MovieModel, movie_update: MovieUpdateSchema) -> None:
    update_data = movie_update.model_dump(exclude_unset=True, exclude_none=True)

    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()


async def remove_movie(db: AsyncSession, db_movie: MovieModel):
    await db.delete(db_movie)
    await db.commit()
