from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieModel
from schemas import MovieCreate, MovieUpdateSchema


async def get_movies_list(
        db: AsyncSession,
        page: int,
        per_page: int
):
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar()

    total_pages = (total_items + per_page - 1) // per_page if total_items else 0

    offset = (page - 1) * per_page

    result = await db.execute(select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page))
    movies = result.scalars().all()

    return {
        "movies": movies,
        "prev_page": f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "next_page": f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def create_movie(
        db: AsyncSession,
        movie: MovieCreate,
):
    existing_movies = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date))
    if existing_movies.scalar_one_or_none():
        raise HTTPException(status_code=409,
                            detail=f"A movie with the name '{movie.name}' "
                                   f"and release date '{movie.date}' already exists.")

    new_movie = MovieModel(**movie.model_dump(
        exclude={"genres", "actors", "languages", "country"}
    ))

    genres = await db.execute(select(GenreModel))
    existing_genres = {genre.name: genre for genre in genres.scalars().all()}

    genres_obj = []

    for genre_name in movie.genres:
        if genre_name in existing_genres:
            genres_obj.append(existing_genres[genre_name])
        else:
            new_genre = GenreModel(name=genre_name)
            db.add(new_genre)
            await db.flush()
            genres_obj.append(new_genre)

    new_movie.genres = genres_obj

    actors = await db.execute(select(ActorModel))
    existing_actors = {actors.name: actors for actors in actors.scalars().all()}

    actors_obj = []

    for actor_name in movie.actors:
        if actor_name in existing_actors:
            actors_obj.append(existing_actors[actor_name])
        else:
            new_actor = ActorModel(name=actor_name)
            db.add(new_actor)
            await db.flush()
            actors_obj.append(new_actor)

    new_movie.actors = actors_obj

    languages = await db.execute(select(LanguageModel))
    existing_languages = {languages.name: languages for languages in languages.scalars().all()}

    languages_obj = []

    for language_name in movie.languages:
        if language_name in existing_languages:
            languages_obj.append(existing_languages[language_name])
        else:
            new_language = LanguageModel(name=language_name)
            db.add(new_language)
            await db.flush()
            languages_obj.append(new_language)

    new_movie.languages = languages_obj

    country_code = movie.country.upper()

    result = await db.execute(
        select(CountryModel).where(CountryModel.code == country_code)
    )
    existing_country = result.scalar_one_or_none()

    if existing_country:
        new_movie.country = existing_country
    else:
        new_country = CountryModel(
            code=country_code,
            name=None
        )
        db.add(new_country)
        await db.flush()
        new_movie.country = new_country

    db.add(new_movie)
    await db.commit()
    stmt = select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ).where(MovieModel.id == new_movie.id)

    result = await db.execute(stmt)
    movie_with_relations = result.scalar_one()

    return movie_with_relations


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    return movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    await db.delete(movie)
    await db.commit()


async def update_movie(db: AsyncSession, movie_id: int, movie_update: MovieUpdateSchema):
    result = await db.execute(select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)).where(MovieModel.id == movie_id))

    movie_db = result.scalar_one_or_none()

    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie_db, key, value)

    await db.commit()
    await db.refresh(movie_db)

    return {"detail": "Movie updated successfully."}
