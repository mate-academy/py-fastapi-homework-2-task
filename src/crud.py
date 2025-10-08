from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreate, MovieUpdate


async def create_movie(db: AsyncSession, movie: MovieCreate):
    country_result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for genre_name in movie.genres:
        genre_result = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
        genre = genre_result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genres.append(genre)
    
    actors = []
    for actor_name in movie.actors:
        actor_result = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
        actor = actor_result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actors.append(actor)
    
    languages = []
    for language_name in movie.languages:
        language_result = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
        language = language_result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()
        languages.append(language)
    
    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id
    )
    
    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages
    
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    return result.unique().scalar_one()


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    return result.unique().scalar_one_or_none()


async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_movies_count(db: AsyncSession):
    result = await db.execute(select(func.count(MovieModel.id)))
    return result.scalar()


async def check_movie_exists(db: AsyncSession, name: str, date):
    result = await db.execute(
        select(MovieModel).where(
            and_(MovieModel.name == name, MovieModel.date == date)
        )
    )
    return result.scalar_one_or_none() is not None


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    update_data = movie.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)
    
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
