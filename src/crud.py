from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieListItemSchema
from schemas.movies import (
    MovieCreate,
    CountryCreateSchema,
    GenreCreateSchema,
    ActorCreateSchema,
    LanguageCreateSchema,
    MovieUpdate
)


async def get_movies(
    per_page: int,
    page: int,
    db: AsyncSession
):

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.country)
    ).order_by(MovieModel.id.desc())

    query = query.offset((page - 1) * per_page).limit(per_page)

    movie_list = await db.execute(query)
    movies = movie_list.unique().scalars().all()
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    if not movies:
        return None
    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(movie) for movie in movies],
        total_pages=total_pages,
        total_items=total_items,
        prev_page=prev_page,
        next_page=next_page
    )


async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.country)
    ).where(MovieModel.id == movie_id)

    result = await db.execute(query)
    movie = result.unique().scalar_one_or_none()
    if not movie:
        return None
    return movie


async def validate_movie_data(movie: MovieCreate):
    now = datetime.now().date()
    if movie.date > now + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Date cannot be in the future.")
    if len(movie.name) > 255:
        raise HTTPException(status_code=400, detail=f"Movie {movie.name} cannot be longer than 255 characters.")
    if not 0 <= movie.score <= 100:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100.")
    if movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Budget and revenue must be positive.")


async def create_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    # Check if country_code or country is provided
    if movie.country_code:
        country_code = movie.country_code
    elif movie.country:
        country_code = movie.country
    else:
        raise HTTPException(
            status_code=400,
            detail="Country code is required. Please provide a value for 'country' field."
        )

    country_query = await db.execute(select(CountryModel).where(CountryModel.code == country_code))
    country = country_query.scalar_one_or_none()
    if not country:
        country = CountryModel(
            code=country_code,
            name=None
        )
        db.add(country)
        if country.name and len(country.name) > 255:
            raise HTTPException(status_code=400, detail=f"Movie {country.name} cannot be longer than 255 characters.")
        await db.commit()
        await db.refresh(country)

    genres = []
    if movie.genres:
        for genre_name in movie.genres:
            if len(genre_name) > 255:
                raise HTTPException(status_code=400,
                                    detail=f"Genre name '{genre_name}' cannot be longer than 255 characters.")
            genre_query = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
            genre = genre_query.scalar_one_or_none()

            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.commit()
                await db.refresh(genre)

            genres.append(genre)

    actors = []
    if movie.actors:
        for actor_name in movie.actors:
            if len(actor_name) > 255:
                raise HTTPException(status_code=400,
                                    detail=f"Movie {actor_name} cannot be longer than 255 characters.")
            actor_query = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
            actor = actor_query.scalar_one_or_none()

            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.commit()
                await db.refresh(actor)

            actors.append(actor)

    languages = []
    if movie.languages:
        for language_name in movie.languages:
            if len(language_name) > 255:
                raise HTTPException(status_code=400,
                                    detail=f"Movie {language_name} cannot be longer than 255 characters.")
            language_query = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
            language = language_query.scalar_one_or_none()

            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.commit()
                await db.refresh(language)

            languages.append(language)

    movie_data = movie.model_dump(exclude={
        "genre_ids", "actor_ids", "language_ids",
        "genre_name", "actor_name", "language_name",
        "country_code", "country", "genres", "actors", "languages"
    })

    # Set country_id
    movie_data["country_id"] = country.id

    # Create new movie
    new_movie = MovieModel(**movie_data)

    # Set relationships
    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages

    existing_movie = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    if existing_movie.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.")

    db.add(new_movie)
    await db.commit()

    # Reload the movie with all relationships eagerly loaded
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.country)
    ).where(MovieModel.id == new_movie.id)

    result = await db.execute(query)
    loaded_movie = result.unique().scalar_one_or_none()

    return loaded_movie


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.country)
    ).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    db_movie = result.unique().scalar_one_or_none()
    if not db_movie:
        return None
    update_data = movie.model_dump(exclude_unset=True, exclude={
        "genre_ids", "actor_ids", "language_ids",
        "genre_name", "actor_name", "language_name",
        "country_code", "country", "genres", "actors", "languages"
    })

    for field, value in update_data.items():
        if value is not None:  # оновлюємо тільки непорожні значення
            setattr(db_movie, field, value)

    if movie.genres is not None:
        db_movie.genres.clear()
        for genre_name in movie.genres:
            genre_query = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
            genre = genre_query.scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            db_movie.genres.append(genre)

    if movie.actors is not None:
        db_movie.actors.clear()
        for actor_name in movie.actors:
            actor_query = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
            actor = actor_query.scalar_one_or_none()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()

            db_movie.actors.append(actor)

    if movie.languages is not None:
        db_movie.languages.clear()
        for language_name in movie.languages:
            language_query = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
            language = language_query.scalar_one_or_none()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()

            db_movie.languages.append(language)

    if movie.country:
        # First try to find country by name
        country_query = await db.execute(select(CountryModel).where(CountryModel.name == movie.country))
        country = country_query.scalar_one_or_none()

        if not country:
            # If not found by name, try to find by code (assuming country might be a code)
            country_query = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
            country = country_query.scalar_one_or_none()

            if not country:
                # If still not found, create a new country with the value as both code and name
                country = CountryModel(code=movie.country, name=movie.country)
                db.add(country)
                await db.flush()

        db_movie.country = country

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.country)
    ).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    db_movie = result.unique().scalar_one_or_none()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie
