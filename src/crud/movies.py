from typing import Tuple, List

from fastapi import HTTPException

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, noload

from database import MovieModel
from database.models import (
    GenreModel,
    ActorModel,
    LanguageModel,
    CountryModel
)
from schemas.movies import (
    MovieCreateSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieUpdateSchema
)
from utils.pagination import (
    get_paginated_items,
    get_total_items,
    get_pagination_links
)


async def get_or_create_entity(
        db: AsyncSession,
        model: type,
        name: str
) -> int:
    stmt = select(model).where(model.name == name)
    result = await db.execute(stmt)
    entity = result.scalars().first()
    if not entity:
        entity = model(name=name)
        db.add(entity)
        await db.flush()
    return entity.id


async def create_movie(db: AsyncSession, movie: MovieCreateSchema) -> MovieModel:
    stmt = select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and \
            release date '{movie.date}' already exists."
        )

    movie_data = movie.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )
    new_movie = MovieModel(**movie_data)

    stmt = select(CountryModel).where(CountryModel.code == movie.country)
    result = await db.execute(stmt)
    country = result.scalars().first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()
    new_movie.country_id = country.id

    db.add(new_movie)
    await db.flush()

    stmt = select(MovieModel).options(
        noload(MovieModel.genres),
        noload(MovieModel.actors),
        noload(MovieModel.languages)
    ).where(MovieModel.id == new_movie.id)
    result = await db.execute(stmt)
    new_movie = result.scalars().first()

    new_movie.genres = []
    for genre_name in movie.genres:
        genre_id = await get_or_create_entity(db, GenreModel, genre_name)
        genre = await db.get(GenreModel, genre_id)
        new_movie.genres.append(genre)

    new_movie.actors = []
    for actor_name in movie.actors:
        actor_id = await get_or_create_entity(db, ActorModel, actor_name)
        actor = await db.get(ActorModel, actor_id)
        new_movie.actors.append(actor)

    new_movie.languages = []
    for language_name in movie.languages:
        language_id = await get_or_create_entity(
            db,
            LanguageModel,
            language_name
        )
        language = await db.get(LanguageModel, language_id)
        new_movie.languages.append(language)

    try:
        await db.commit()
        await db.refresh(
            new_movie,
            attribute_names=["country", "genres", "actors", "languages"]
        )
        return new_movie
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and \
            release date '{movie.date}' already exists."
        )


async def get_movies_paginated(
        db: AsyncSession,
        page: int,
        per_page: int
) -> Tuple[List[MovieModel], int, int, str | None, str | None]:
    total = await get_total_items(db, MovieModel)

    if total == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page out of range")

    offset = (page - 1) * per_page
    movies = await get_paginated_items(db, MovieModel, offset, per_page)
    movies_schema = [
        MovieListItemSchema.model_validate(movie) for movie in movies
    ]
    prev_page, next_page = get_pagination_links(page, per_page, total_pages)

    return {
        "movies": movies_schema,
        "total_items": total,
        "total_pages": total_pages,
        "prev_page": prev_page,
        "next_page": next_page
    }


async def get_movie_by_id(
        db: AsyncSession,
        movie_id: int
) -> MovieDetailSchema:
    stmt = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    movie_dict = {
        "id": movie.id,
        "name": movie.name,
        "date": movie.date,
        "score": movie.score,
        "overview": movie.overview,
        "status": movie.status,
        "budget": movie.budget,
        "revenue": movie.revenue,
        "country": {
            "id": movie.country.id,
            "code": movie.country.code,
            "name": movie.country.name
        } if movie.country else None,
        "genres": [{"id": genre.id, "name": genre.name} for genre in movie.genres],
        "actors": [{"id": actor.id, "name": actor.name} for actor in movie.actors],
        "languages": [
            {
                "id": language.id,
                "name": language.name
            }
            for language in movie.languages
        ]
    }
    return MovieDetailSchema.model_validate(movie_dict)


async def delete_movie(db: AsyncSession, movie_id: int) -> None:
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


async def update_movie(
        db: AsyncSession,
        movie_id: int,
        movie: MovieUpdateSchema
) -> MovieModel:
    stmt = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie_result = result.scalars().first()
    if not movie_result:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie_result, key, value)

    await db.commit()
    await db.refresh(
        movie_result,
        attribute_names=["country", "genres", "actors", "languages"]
    )
    return movie_result