import datetime

from pydantic import ValidationError
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel
from database.models import MovieStatusEnum, LanguageModel, ActorModel, GenreModel, CountryModel
from schemas import MovieListResponseSchema, MovieCreateSchema
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from schemas.movies import MovieUpdate


async def get_movies(
        db: AsyncSession,
        page: int,
        per_page: int,
):
    offset = (page - 1) * per_page

    total_items_stmt = select(func.count()).select_from(MovieModel)
    result = await db.execute(total_items_stmt)
    total_items = result.scalar_one()

    total_pages = (total_items + per_page - 1) // per_page

    stmt = (
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    prev_page = None if page <= 1 else f"/theater/movies/?page={page - 1}&per_page={per_page}"
    next_page = None if page >= total_pages else f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def get_movie_by_id(db: AsyncSession, movie_id):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()
    return movie


async def create_movie(db: AsyncSession, movie: MovieCreateSchema):
    if isinstance(movie.date, str):
        movie_date = datetime.date.fromisoformat(movie.date)
    else:
        movie_date = movie.date

    new_movie = MovieModel(
        name=movie.name,
        date=movie_date,
        score=movie.score,
        overview=movie.overview,
        status=MovieStatusEnum(movie.status.value),
        budget=movie.budget,
        revenue=movie.revenue,
    )

    question = await db.execute(select(MovieModel).filter_by(name=movie.name))
    existing_movie = question.scalar_one_or_none()

    if existing_movie is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    # Country
    country_obj = await db.scalar(select(CountryModel).filter_by(name=movie.country))
    if not country_obj:
        country_obj = CountryModel(name=movie.country, code=movie.country)
        db.add(country_obj)
        await db.flush()

    new_movie.country = country_obj

    # Genres
    genres = []
    for genre_name in movie.genres:
        genre = await db.scalar(select(GenreModel).filter_by(name=genre_name))
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)
    new_movie.genres = genres

    # Actors
    actors = []
    for actor_name in movie.actors:
        actor = await db.scalar(select(ActorModel).filter_by(name=actor_name))
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)
    new_movie.actors = actors

    # Languages
    languages = []
    for lang_name in movie.languages:
        lang = await db.scalar(select(LanguageModel).filter_by(name=lang_name))
        if not lang:
            lang = LanguageModel(name=lang_name)
            db.add(lang)
            await db.flush()
        languages.append(lang)
    new_movie.languages = languages

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie, ["country", "genres", "actors", "languages"])
    return new_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(db_movie)
    await db.commit()
    return db_movie


async def update_movie_by_id(
        movie_id: int,
        movie_update: MovieUpdate,
        db: AsyncSession
):
    movie_query = select(MovieModel).filter(MovieModel.id == movie_id)
    result = await db.execute(movie_query)
    movie_to_update = result.scalar_one_or_none()

    if movie_to_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    try:
        update_data = movie_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(movie_to_update, key, value)

        await db.commit()
        await db.refresh(movie_to_update)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data: {e.errors()}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input data. Error: {e}"
        )

    return {"detail": "Movie updated successfully."}