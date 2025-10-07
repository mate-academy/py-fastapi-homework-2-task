import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from repository.movies import (
    get_movies,
    get_movies_count,
    get_movie,
    update_movie,
    delete_film,
)
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.errors import NotFoundResponse
from schemas.movies import (
    MovieCreateRequestSchema,
    MovieUpdateSchema,
    MovieUpdateResponseSchema,
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "No movies found.",
            "content": {
                "application/json": {"example": {"detail": "No movies found."}}
            },
        },
    },
)
async def get_movies_list(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await get_movies_count(db)
    total_pages = math.ceil(total_items / per_page)

    if not total_items or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = await get_movies(page, per_page, db)

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    },
)
async def movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
        409: {
            "model": NotFoundResponse,
            "description": "A movie with the those name and release date already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A movie with the those name and release date already exists."
                    }
                }
            },
        },
        400: {
            "model": NotFoundResponse,
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
    },
    status_code=201,
)
async def movie_create(
    movie_data: MovieCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    movie_exists = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name, MovieModel.date == movie_data.date
        )
    )

    if movie_exists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    try:
        country = await db.scalar(
            select(CountryModel).where(CountryModel.code == movie_data.country)
        )
        if not country:
            country = CountryModel(code=movie_data.country, name=None)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie_data.genres:
            genre = await db.scalar(
                select(GenreModel).where(GenreModel.name == genre_name)
            )
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        actors = []
        for actor_name in movie_data.actors:
            actor = await db.scalar(
                select(ActorModel).where(ActorModel.name == actor_name)
            )
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)

        languages = []
        for language_name in movie_data.languages:
            language = await db.scalar(
                select(LanguageModel).where(LanguageModel.name == language_name)
            )
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
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return new_movie


@router.patch(
    "/movies/{movie_id}/",
    response_model=MovieUpdateResponseSchema,
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
        400: {
            "model": NotFoundResponse,
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
        200: {
            "model": MovieUpdateResponseSchema,
            "description": "Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie updated successfully."}
                }
            },
        },
    },
    status_code=200,
)
async def movie_patch(
    movie_data: MovieUpdateSchema, movie_id: int, db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await update_movie(db, movie, movie_data)

    return {"detail": "Movie updated successfully."}


@router.delete(
    "/movies/{movie_id}/",
    responses={
        404: {
            "model": NotFoundResponse,
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    },
    status_code=204,
)
async def movie_delete(movie_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await delete_film(db, movie_id)
    return None
