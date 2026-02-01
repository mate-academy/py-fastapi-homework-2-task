import math
from typing import TypeVar, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, insert, update
from sqlalchemy.orm import selectinload, joinedload

from database import MovieModel
from database.models import GenreModel, ActorModel, LanguageModel, CountryModel, Base
from schemas import (
    MovieCreateSchema,
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
)
from crud.exceptions import ItemDoesNotExist, ItemAlreadyExist, InvalidDataError

T = TypeVar("T", bound=Base)


async def _get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel:
    """Get movie by its id"""
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise ItemDoesNotExist("Such movie does not exist")
    return movie


async def _get_or_create_items_by_names(
    db: AsyncSession, target_model: Type[T], names: list[str]
) -> list[T]:
    """Get or create genres, actors and languages by its names"""
    unique_names = set(names)
    db_items = await db.scalars(
        select(target_model).where(target_model.name.in_(unique_names))
    )
    db_items = list(db_items.all())
    missing = unique_names - {item.name for item in db_items}
    new_items = []
    if missing:
        new_items = await db.scalars(
            insert(target_model).returning(target_model),
            [{"name": name} for name in missing],
        )
        new_items = list(new_items.all())

    return db_items + new_items


async def _get_or_create_country_by_code(
    db: AsyncSession, country_code: str
) -> CountryModel:
    """Get country by name"""

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    if country is None:
        country = CountryModel(code=country_code)
        db.add(country)
        await db.commit()
    return country


async def create_movie(db: AsyncSession, movie_data: MovieCreateSchema) -> MovieModel:
    """Create movie"""
    if (
        not movie_data.genres
        or not movie_data.languages
        or not movie_data.actors
        or not movie_data.country
    ):
        raise InvalidDataError
    genres_db = await _get_or_create_items_by_names(db, GenreModel, movie_data.genres)
    actors_db = await _get_or_create_items_by_names(db, ActorModel, movie_data.actors)
    languages_db = await _get_or_create_items_by_names(
        db, LanguageModel, movie_data.languages
    )
    country_db = await _get_or_create_country_by_code(db, str(movie_data.country))

    if await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    ):
        raise ItemAlreadyExist("Project with this name already exists")

    new_movie = MovieModel(
        **movie_data.model_dump(exclude={"genres", "actors", "languages", "country"}),
        actors=actors_db,
        genres=genres_db,
        languages=languages_db,
        country_id=country_db.id,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(
        new_movie, attribute_names=["country", "genres", "actors", "languages"]
    )

    return new_movie


async def get_movies(db: AsyncSession, page: int, per_page: int) -> list[MovieModel]:
    total_movie_items = await db.scalar(select(func.count("*")).select_from(MovieModel))
    if not total_movie_items:
        raise ItemDoesNotExist("No movies found")

    total_movie_pages = math.ceil(total_movie_items / per_page)

    if total_movie_pages < page:
        raise ItemDoesNotExist("No movies found")

    movie_list = await db.scalars(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    movie_list = list(movie_list.all())
    movie_list_data = {
        "movies": movie_list,
        "total_pages": total_movie_pages,
        "total_items": total_movie_items,
    }
    if page > 1:
        prev_url = f"/theater/movies/?page={page - 1}&per_page={per_page}"
        movie_list_data["prev_page"] = prev_url
    if page < total_movie_pages:
        next_url = f"/theater/movies/?page={page + 1}&per_page={per_page}"
        movie_list_data["next_page"] = next_url

    result = MovieListResponseSchema(**movie_list_data)
    return result


async def read_movie_detail(db: AsyncSession, movie_id: int) -> MovieModel:
    movie = await db.get(
        MovieModel,
        movie_id,
        options=[
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            joinedload(MovieModel.country),
        ],
    )

    if movie is None:
        raise ItemDoesNotExist("Movie not found")
    return movie


async def delete_movie_by_id(db: AsyncSession, movie_id: int) -> None:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise ItemDoesNotExist("Movie not found")
    await db.delete(movie)
    await db.commit()


async def update_movie_by_id(
    db: AsyncSession, movie_data: MovieUpdateSchema, movie_id: int
) -> None:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise ItemDoesNotExist("Movie not found")

    update_data = movie_data.model_dump(exclude_unset=True)

    await db.execute(
        update(MovieModel).where(MovieModel.id == movie_id).values(**update_data)
    )

    await db.commit()
    await db.refresh(movie)
