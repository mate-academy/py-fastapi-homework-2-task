from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database import MovieModel
from database.models import GenreModel, LanguageModel, CountryModel, ActorModel
from database.session_sqlite import AsyncSQLiteSessionLocal
from schemas.movies import MovieCreateSchema


async def create_movie(movie: MovieCreateSchema, db: AsyncSQLiteSessionLocal):
    data = movie.model_dump()

    movie_name = data.get("name")
    movie_date = data.get("date")
    country_code = data.pop("country", None)
    genres = []
    actors = []
    languages = []

    existing_movie = await db.scalar(select(MovieModel).where(MovieModel.name == movie_name, MovieModel.date == movie_date))

    if existing_movie:
        raise HTTPException(status_code=404, detail="Movie already exists.")


    for actor_name in data.pop("actors", []):
        db_actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == actor_name)
        )

        if db_actor is None:
            db_actor = ActorModel(name=actor_name)

        actors.append(db_actor)

    for genre_name in data.pop("genres", []):
        db_genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))

        if db_genre is None:
            db_genre = GenreModel(name=genre_name)

        genres.append(db_genre)

    for language_name in data.pop("languages", []):
        db_language = await db.scalar(select(LanguageModel).where(LanguageModel.name == language_name))

        if db_language is None:
            db_language = LanguageModel(name=language_name)

        languages.append(db_language)

    country = None

    if country_code:
        db_country = await db.scalar(select(CountryModel).where(CountryModel.code == country_code))

        if db_country is None:
            db_country = CountryModel(code=country_code, name=None)

        country = db_country

    db_movie = MovieModel(
        **data,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(db_movie)
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == db_movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    return result.scalar_one()
