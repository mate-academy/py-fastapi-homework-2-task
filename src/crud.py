from fastapi import HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema


async def get_movie(
        movie_id: int,
        db: AsyncSession
):
    result = await (db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    ))
    movie = result.scalars().first()
    return movie


async def get_all_movies_paginated(
        db: AsyncSession,
        page: int,
        per_page: int
):
    offset = (page - 1) * per_page

    result = await db.execute(select(MovieModel).order_by(desc(MovieModel.id)))
    all_movies = result.scalars().all()

    movies = all_movies[offset:offset + per_page]
    total_items = len(all_movies)
    total_pages = total_items // per_page + (
        1 if total_items % per_page != 0 else 0
    )

    if page <= 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page >= total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


async def create_movie(movie: MovieCreateSchema, db: AsyncSession):

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue
    )

    country = await db.execute(
        select(CountryModel).filter(CountryModel.code == movie.country)
    )
    country = country.scalars().first()

    if not country:
        country = CountryModel(
            code=movie.country,
            name=None
        )
        db.add(country)


    genres = []
    for genre_name in movie.genres:
        genre = await db.execute(
            select(GenreModel).filter(GenreModel.name == genre_name)
        )
        genre = genre.scalars().first()

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)

        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = await db.execute(
            select(ActorModel).filter(ActorModel.name == actor_name)
        )
        actor = actor.scalars().first()

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)

        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = await db.execute(
            select(LanguageModel).filter(LanguageModel.name == language_name)
        )
        language = language.scalars().first()

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)

        languages.append(language)

    # new_movie.country_id = country.id
    new_movie.country = country
    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie
