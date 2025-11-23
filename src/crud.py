import math

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from src.database.models import MovieModel, GenreModel, ActorModel, LanguageModel
from src.schemas.movies import MovieCreate, MovieUpdate, MovieListResponse, MovieDetail, MovieListItem


async def create_movie(db: AsyncSession, movie: MovieCreate):
    data = movie.model_dump(exclude={"genres", "actors", "languages"})
    new_movie = MovieModel(**data)
    db.add(new_movie)
    await db.flush()

    db_genres_query = await db.execute(
        select(GenreModel).where(GenreModel.name.in_(movie.genres))
    )
    db_genres = db_genres_query.scalars().all()
    existing_names = [genre.name for genre in db_genres]
    missing_names = [genre for genre in movie.genres if genre not in existing_names]

    new_genres = []
    for name in missing_names:
        genre = GenreModel(name=name)
        db.add(genre)
        new_genres.append(genre)

    await db.flush()
    all_genres = db_genres + new_genres
    new_movie.genres = all_genres

    db_actors_query = await db.execute(
        select(ActorModel).where(ActorModel.name.in_(movie.actors))
    )
    db_actors = db_actors_query.scalars().all()
    existing_names = [actor.name for actor in db_actors]
    missing_names = [actor for actor in movie.actors if actor not in existing_names]

    new_actors = []
    for name in missing_names:
        actor = ActorModel(name=name)
        db.add(actor)
        new_actors.append(actor)

    await db.flush()
    all_actors = db_actors + new_actors
    new_movie.actors = all_actors

    db_languages_query = await db.execute(
        select(LanguageModel).where(LanguageModel.name.in_(movie.languages))
    )
    db_languages = db_languages_query.scalars().all()
    existing_names = [language.name for language in db_languages]
    missing_names = [language for language in movie.languages if language not in existing_names]

    new_languages = []
    for name in missing_names:
        language = LanguageModel(name=name)
        db.add(language)
        new_languages.append(language)

    await db.flush()
    all_languages = db_languages + new_languages
    new_movie.languages = all_languages

    await db.commit()
    await db.refresh(new_movie)
    return new_movie


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    return movie


async def get_movies(db: AsyncSession, page: int, per_page: int):

    offset = (page - 1) * per_page
    total_items_query = select(func.count()).select_from(MovieModel)
    total_items_result = await db.execute(total_items_query)
    total_items = total_items_result.scalar_one_or_none()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page))

    movies = result.scalars().all()

    movie_items = [
        MovieListItem.model_validate(m, from_attributes=True)
        for m in movies
    ]

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponse(
        movies=movie_items,
        total_items=total_items,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
    )


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    update_data = movie.model_dump(exclude_unset=True)

    scalar_fields = [
        "name",
        "date",
        "score",
        "overview",
        "status",
        "budget",
        "revenue",
        "country_id",
    ]

    for field in scalar_fields:
        if field in update_data:
            setattr(db_movie, field, update_data[field])

    if "genres" in update_data:
        genre_names = update_data["genres"] or []
        if genre_names:
            result = await db.execute(
                select(GenreModel).where(GenreModel.name.in_(genre_names))
            )
            db_movie.genres = list(result.scalars().all())
        else:
            db_movie.genres.clear()

    if "actors" in update_data:
        actor_names = update_data["actors"] or []
        if actor_names:
            result = await db.execute(
                select(ActorModel).where(ActorModel.name.in_(actor_names))
            )
            db_movie.actors = list(result.scalars().all())
        else:
            db_movie.actors.clear()

    if "languages" in update_data:
        language_names = update_data["languages"] or []
        if language_names:
            result = await db.execute(
                select(LanguageModel).where(LanguageModel.name.in_(language_names))
            )
            db_movie.languages = list(result.scalars().all())
        else:
            db_movie.languages.clear()

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None
    await db.delete(db_movie)
    await db.commit()
    return db_movie
