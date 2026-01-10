import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from more_itertools.recipes import unique
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieUpdate, \
    MovieCreate, MovieDetailRead, MovieListItem

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListItem)
async def get_movies(page: int = Query(1, ge=1, description="Page number (starting from 1)"),
                     per_page: int = Query(10, ge=1, le=20, description="Items per page"),
                     db: AsyncSession = Depends(get_db)
                     ):
    count_query = select(func.count().select_from(MovieModel))
    count_results = await db.execute(count_query)
    total_items = count_results.scalar_one_or_none()

    if total_items == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page} not found. Total pages: {total_pages}"
        )

    offset = (page - 1) * per_page

    query = select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    results = await db.execute(query)
    movies = results.scalars().all()

    base_url = "/theater/movies"

    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListItem(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/{movie_id}", response_model=MovieDetailRead)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(movie)
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return db_movie


async def get_or_create_country(db: AsyncSession, name: str):
    stmt = select(CountryModel).where(CountryModel.name == name)
    result = await db.execute(stmt)
    country = result.scalar_one_or_none()
    if country is None:
        country = CountryModel(name=name)
        db.add(country)
        await db.flush()
    return country


async def get_or_create_genre(db: AsyncSession, name: str):
    stmt = select(GenreModel).where(GenreModel.name == name)
    result = await db.execute(stmt)
    genre = result.scalar_one_or_none()
    if genre is None:
        genre = GenreModel(name=name)
        db.add(genre)
        await db.flush()
    return genre


async def get_or_create_actor(db: AsyncSession, name: str):
    stmt = select(ActorModel).where(ActorModel.name == name)
    result = await db.execute(stmt)
    actor = result.scalar_one_or_none()
    if actor is None:
        actor = ActorModel(name=name)
        db.add(actor)
        await db.flush()
    return actor


async def get_or_create_language(db: AsyncSession, name: str):
    stmt = select(LanguageModel).where(LanguageModel.name == name)
    result = await db.execute(stmt)
    language = result.scalar_one_or_none()
    if language is None:
        language = LanguageModel(name=name)
        db.add(language)
        await db.flush()
    return language


@router.post("/", response_model=MovieListItem, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date,
    )
    result = await db.execute(query)

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid input data.")
    movie = MovieModel(**movie_in.model_dump())

    country = await get_or_create_country(db, movie_in.country)

    unique_genres = list(set(movie_in.genres))
    unique_actors = list(set(movie_in.actors))
    unique_languages = list(set(movie_in.languages))

    genres_tasks = [get_or_create_genre(db, name) for name in unique_genres]
    actors_tasks = [get_or_create_actor(db, name) for name in unique_actors]
    languages_tasks = [get_or_create_language(db, name) for name in unique_languages]

    genres = await asyncio.gather(*genres_tasks, )
    actors = await asyncio.gather(*actors_tasks, )
    languages = await asyncio.gather(*languages_tasks, )

    for items, name in [(genres, "genres"), (actors, "actors"), (languages, "languages")]:
        for item in items:
            if isinstance(item, Exception):
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create {name}: {str(item)}"
                )

    movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status.value if hasattr(movie_in.status, 'value') else movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie, attribute_names=["genres", "actors", "languages", "country"])
    return movie


@router.patch("/{movie_id}", response_model=MovieListItem, status_code=status.HTTP_202_ACCEPTED)
async def update_movie(movie_id: int, movie_in: MovieUpdate, db: AsyncSession = Depends(get_db)):
    movie = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(movie)
    db_movie = result.scalar_one_or_none()

    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    update_data = movie_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)
    return {"detail": "Movie updated successfully."}


@router.delete("/{movie_id}", response_model=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(movie)
    db_movie = result.scalar_one_or_none()

    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    await db.delete(db_movie)
    await db.commit()

    return None
