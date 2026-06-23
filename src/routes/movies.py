import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MoviePatchSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movie_list(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
) -> MovieListResponseSchema:
    offset = (page - 1) * per_page
    movies = (
        await db.scalars(
            select(MovieModel)
            .order_by(desc(MovieModel.id))
            .offset(offset)
            .limit(per_page)
        )
    ).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await db.scalar(select(func.count(MovieModel.id)))

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page * per_page < total_items:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    total_pages = math.ceil(total_items / per_page)

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


async def get_or_create_country(db: AsyncSession, country_code: str) -> CountryModel:
    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code)
    )

    if country is None:
        country = CountryModel(code=country_code)
        db.add(country)

    return country


async def get_or_create_genre(db: AsyncSession, genre_name: str) -> GenreModel:
    genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))

    if genre is None:
        genre = GenreModel(name=genre_name)
        db.add(genre)

    return genre


async def get_or_create_actor(db: AsyncSession, actor_name: str) -> ActorModel:
    actor = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))

    if actor is None:
        actor = ActorModel(name=actor_name)
        db.add(actor)

    return actor


async def get_or_create_language(db: AsyncSession, language_name: str) -> LanguageModel:
    language = await db.scalar(
        select(LanguageModel).where(LanguageModel.name == language_name)
    )

    if language is None:
        language = LanguageModel(name=language_name)
        db.add(language)

    return language


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    db_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )

    if db_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' "
            f"and release date '{movie_data.date}' already exists.",
        )

    country = await get_or_create_country(db, movie_data.country)

    genres = []
    for genre_name in movie_data.genres:
        genre = await get_or_create_genre(db, genre_name)
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = await get_or_create_actor(db, actor_name)
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = await get_or_create_language(db, language_name)
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
    await db.refresh(new_movie)

    query = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    movie = await db.scalar(query)
    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieModel:
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    movie = await db.scalar(query)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, movie_data: MoviePatchSchema, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> None:
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return
