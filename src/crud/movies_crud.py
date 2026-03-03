from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud import countries_crud, generic_crud
from database import MovieModel
from database.models import ActorModel, GenreModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieDetailSchema


async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession):
    response_actors = await generic_crud.fetch_or_create_entities(movie_data.actors, ActorModel, db)
    response_country = await countries_crud.fetch_or_create_countries(movie_data.country, db)
    response_genres = await generic_crud.fetch_or_create_entities(movie_data.genres, GenreModel, db)
    response_languages = await generic_crud.fetch_or_create_entities(movie_data.languages, LanguageModel, db)

    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        )
    )

    if existing_movie.scalars().first():
        raise HTTPException(status_code=409, detail=f"A movie with the name '{movie_data.name}'"
                                                    f" and release date '{movie_data.date}' already exists.")

    movie = MovieModel(**movie_data.model_dump(exclude={"actors", "country", "genres", "languages"}))
    movie.actors = response_actors
    movie.country = response_country
    movie.genres = response_genres
    movie.languages = response_languages
    db.add(movie)

    await db.commit()
    await db.refresh(movie)

    movie_query = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.actors),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
        .where(MovieModel.id == movie.id)
    )
    movie_with_rel = movie_query.scalars().first()

    return MovieDetailSchema.model_validate(movie_with_rel)
