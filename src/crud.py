from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta
from fastapi import HTTPException, Depends

from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    LanguageModel,
    ActorModel)

from schemas.movies import (
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)



async def create_movie(db: AsyncSession, movie_data: MovieCreateSchema):
    existing_stmt =select(MovieModel).where(
        (MovieModel.name == movie_data.name), (MovieModel.date == movie_data.date)
    )
    result = await db.execute(existing_stmt)
    existing_movie = result.scalars().first()

    if existing_movie:
        raise HTTPException(
            status_code=409, detail=f"A movie with the name '{existing_movie.name}' and release date "
                                    f"'{existing_movie.date}' already exists."
        )
    try:
        country_stmt = select(CountryModel).where(CountryModel.code == movie_data.country)
        country_result = await db.execute(country_stmt)
        country = country_result.scalars().first()
        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalars().first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        actors = []
        for actor_name in movie_data.actors:
            actor_stmt = select(ActorModel).where(ActorModel.name == actor_name)
            actor_result = await db.execute(actor_stmt)
            actor = actor_result.scalars().first()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)

        languages = []
        for language_name in movie_data.languages:
            language_stmt = select(LanguageModel).where(LanguageModel.name == language_name)
            language_result = await db.execute(language_stmt)
            language = language_result.scalars().first()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()
            languages.append(language)

        new_movie = MovieModel(
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
        languages=languages,
    )
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie, ["genres", "actors", "languages"])

        return MovieDetailSchema.model_validate(new_movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")



async def update_movie(db: AsyncSession, movie_id: int, movie_update: MovieUpdateSchema):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.genres),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return movie


async def delete_movie_crud(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalars().first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(db_movie)
    await db.commit()
    return {"detail": "Movie deleted successfully."}

