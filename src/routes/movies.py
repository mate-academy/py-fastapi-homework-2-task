from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from typing import Optional
import math

from src.database import get_db
from src.database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from src.database.models import MoviesGenresModel, ActorsMoviesModel, MoviesLanguagesModel
from src.schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieStatus
)

router = APIRouter()


# Helper function to get or create related entities
async def get_or_create_country(db: AsyncSession, country_code: str) -> CountryModel:
    """Get existing country or create a new one."""
    code = country_code.upper().strip()

    stmt = select(CountryModel).where(CountryModel.code == code)
    result = await db.execute(stmt)
    country = result.scalar_one_or_none()

    if not country:
        country = CountryModel(code=country_code.upper(), name=None)
        db.add(country)
        await db.flush()

    return country


async def get_or_create_genres(db: AsyncSession, genre_names: list[str]) -> list[GenreModel]:
    """Get existing genres or create new ones."""
    genres = []
    for genre_name in genre_names:
        stmt = select(GenreModel).where(GenreModel.name == genre_name)
        result = await db.execute(stmt)
        genre = result.scalar_one_or_none()

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()

        genres.append(genre)

    return genres


async def get_or_create_actors(db: AsyncSession, actor_names: list[str]) -> list[ActorModel]:
    """Get existing actors or create new ones."""
    actors = []
    for actor_name in actor_names:
        stmt = select(ActorModel).where(ActorModel.name == actor_name)
        result = await db.execute(stmt)
        actor = result.scalar_one_or_none()

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()

        actors.append(actor)

    return actors


async def get_or_create_languages(db: AsyncSession, language_names: list[str]) -> list[LanguageModel]:
    """Get existing languages or create new ones."""
    languages = []
    for language_name in language_names:
        stmt = select(LanguageModel).where(LanguageModel.name == language_name)
        result = await db.execute(stmt)
        language = result.scalar_one_or_none()

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()

        languages.append(language)

    return languages


# Task 1: Implement Movies List Endpoint
@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a paginated list of movies sorted by ID in descending order.
    """
    # Calculate offset
    offset = (page - 1) * per_page

    # Get total count of movies
    count_stmt = select(func.count(MovieModel.id))
    result = await db.execute(count_stmt)
    total_items = result.scalar_one()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Calculate total pages
    total_pages = math.ceil(total_items / per_page)

    # Check if page exists
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Get movies for current page
    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    # Build response
    movie_list = [
        MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview
        )
        for movie in movies
    ]

    # Build pagination links
    base_url = "/theater/movies/"
    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"{base_url}?page={page - 1}&per_page={per_page}"

    if page < total_pages:
        next_page = f"{base_url}?page={page + 1}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=movie_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


# Task 3: Implement Movie Details Endpoint
@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve detailed information about a specific movie by its ID.
    """
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)


# Task 2: Implement Movie Creation Endpoint
@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new movie with related entities.
    """
    # Check for duplicate movie
    stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    )
    result = await db.execute(stmt)
    existing_movie = result.scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # Get or create country
    country = await get_or_create_country(db, movie_data.country)

    # Get or create genres, actors, languages
    genres = await get_or_create_genres(db, movie_data.genres)
    actors = await get_or_create_actors(db, movie_data.actors)
    languages = await get_or_create_languages(db, movie_data.languages)

    # Create new movie
    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status.value,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(new_movie)
    await db.flush()

    # Refresh with relationships loaded
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    result = await db.execute(stmt)
    created_movie = result.scalar_one()

    await db.commit()

    return MovieDetailSchema.model_validate(created_movie)


# Task 4: Implement Movie Deletion Endpoint
@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific movie by its ID.
    """
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None


# Task 5: Implement Movie Update Endpoint
@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int,
    update_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a specific movie's details (partial update).
    """
    # Check if movie exists
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)

    if update_dict:
        # Handle enum conversion for status
        if 'status' in update_dict and update_dict['status']:
            update_dict['status'] = update_dict['status'].value

        # Perform update
        stmt = (
            update(MovieModel)
            .where(MovieModel.id == movie_id)
            .values(**update_dict)
        )
        await db.execute(stmt)
        await db.commit()

    return {"detail": "Movie updated successfully."}
