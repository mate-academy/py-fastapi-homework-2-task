from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    GenreSchema,
    ActorSchema,
    LanguageSchema,
    CountrySchema
)


router = APIRouter()


async def get_or_create_genre(db: AsyncSession, genre_name: str) -> GenreModel:
    genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
    genre_result = await db.execute(genre_stmt)
    genre = genre_result.scalars().first()
    if not genre:
        genre = GenreModel(name=genre_name)
        db.add(genre)
        await db.flush()
    return genre


async def get_or_create_actor(db: AsyncSession, actor_name: str) -> ActorModel:
    actor_stmt = select(ActorModel).where(ActorModel.name == actor_name)
    actor_result = await db.execute(actor_stmt)
    actor = actor_result.scalars().first()
    if not actor:
        actor = ActorModel(name=actor_name)
        db.add(actor)
        await db.flush()
    return actor


async def get_or_create_language(db: AsyncSession, language_name: str) -> LanguageModel:
    language_stmt = select(LanguageModel).where(LanguageModel.name == language_name)
    language_result = await db.execute(language_stmt)
    language = language_result.scalars().first()
    if not language:
        language = LanguageModel(name=language_name)
        db.add(language)
        await db.flush()
    return language


async def get_or_create_country(db: AsyncSession, country_code: str) -> CountryModel:
    country_stmt = select(CountryModel).where(CountryModel.code == country_code)
    country_result = await db.execute(country_stmt)
    country = country_result.scalars().first()
    if not country:
        country = CountryModel(code=country_code, name=None)
        db.add(country)
        await db.flush()
    return country


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    # Get total count
    count_stmt = select(func.count(MovieModel.id))
    count_result = await db.execute(count_stmt)
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    # Check if page exceeds total pages
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Calculate offset
    offset = (page - 1) * per_page

    # Get movies sorted by id descending
    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    # Generate pagination links
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    # Check for duplicate movie (name + date)
    duplicate_stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    )
    duplicate_result = await db.execute(duplicate_stmt)
    if duplicate_result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # Get or create country
    country = await get_or_create_country(db, movie_data.country)

    # Get or create genres
    genre_models = [await get_or_create_genre(db, genre_name) for genre_name in movie_data.genres]

    # Get or create actors
    actor_models = [await get_or_create_actor(db, actor_name) for actor_name in movie_data.actors]

    # Get or create languages
    language_models = [await get_or_create_language(db, language_name) for language_name in movie_data.languages]

    # Create movie
    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id
    )
    movie.genres = genre_models
    movie.actors = actor_models
    movie.languages = language_models

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    # Load relationships
    await db.refresh(movie, ["country", "genres", "actors", "languages"])

    return MovieDetailSchema.model_validate(movie)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    # Update fields if provided
    if movie_data.name is not None:
        movie.name = movie_data.name
    if movie_data.date is not None:
        movie.date = movie_data.date
    if movie_data.score is not None:
        movie.score = movie_data.score
    if movie_data.overview is not None:
        movie.overview = movie_data.overview
    if movie_data.status is not None:
        movie.status = movie_data.status
    if movie_data.budget is not None:
        movie.budget = movie_data.budget
    if movie_data.revenue is not None:
        movie.revenue = movie_data.revenue

    # Update country if provided
    if movie_data.country is not None:
        country = await get_or_create_country(db, movie_data.country)
        movie.country_id = country.id

    # Update genres if provided
    if movie_data.genres is not None:
        movie.genres = [await get_or_create_genre(db, genre_name) for genre_name in movie_data.genres]

    # Update actors if provided
    if movie_data.actors is not None:
        movie.actors = [await get_or_create_actor(db, actor_name) for actor_name in movie_data.actors]

    # Update languages if provided
    if movie_data.languages is not None:
        movie.languages = [await get_or_create_language(db, language_name) for language_name in movie_data.languages]

    await db.commit()
    await db.refresh(movie, ["country", "genres", "actors", "languages"])

    return {"detail": "Movie updated successfully."}
