from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailSchema
from crud import movies as crud
from schemas.movies import (
    MovieCreateSchema,
    CountryCreateSchema,
    GenreCreateSchema,
    ActorCreateSchema,
    LanguageCreateSchema, MovieUpdateSchema
)

router = APIRouter()


@router.get(
    "/movies/", response_model=MovieListResponseSchema, responses={
        404: {
            "description": "No movies found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            }
        }
    }
)
async def get_movies(
    page: Annotated[
        int, Query(ge=1, description="The page number to fetch")
    ] = 1,
    per_page: Annotated[
        int, Query(
            ge=1, le=20, description="Number of movies to fetch per page"
        )
    ] = 10,
    db: AsyncSession = Depends(get_db)
):
    movies, total_items = await crud.get_movies(
        db=db, page=page, per_page=per_page
    )
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail=f"No movies found for the specified page."
        )

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=201,
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The input data is invalid (e.g., "
                                  "missing required fields, invalid values)."
                    }
                }
            }
        },
        409: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A movie with the name 'MovieName' and "
                                  "release date 'Date' already exist"
                    }
                }
            }
        }
    }
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    existing_movie = await crud.get_movie_by_name_date(
        db=db, movie_name=movie_data.name, movie_date=movie_data.date
    )

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name {movie_data.name} "
                   f"and release date {movie_data.date} already exist"
        )

    genres_obj = []
    actors_obj = []
    languages_obj = []

    country = await crud.get_country_by_code(
        db=db,
        county_code=movie_data.country
    )
    if not country:
        country_schema = CountryCreateSchema(code=movie_data.country)
        country = await crud.create_country(db=db, country=country_schema)

    for genre_name in movie_data.genres:
        genre = await crud.get_genre_by_name(db=db, genre_name=genre_name)
        if not genre:
            genre_schema = GenreCreateSchema(name=genre_name)
            genre = await crud.create_genre(db=db, genre=genre_schema)
        genres_obj.append(genre)

    for actor_name in movie_data.actors:
        actor = await crud.get_actor_by_name(db=db, actor_name=actor_name)
        if not actor:
            actor_schema = ActorCreateSchema(name=actor_name)
            actor = await crud.create_actor(db=db, actor=actor_schema)
        actors_obj.append(actor)

    for language_name in movie_data.languages:
        language = await crud.get_language_by_name(
            db=db, language_name=language_name
        )
        if not language:
            language_schema = LanguageCreateSchema(name=language_name)
            language = await crud.create_language(
                db=db, language=language_schema
            )
        languages_obj.append(language)

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres_obj,
        actors=actors_obj,
        languages=languages_obj,
    )

    try:
        db.add(new_movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="The input data is invalid "
                   "(e.g., missing required fields, invalid values)."
        )
    else:
        await db.refresh(new_movie)
        query = (
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
            .where(MovieModel.id == new_movie.id)
        )
        result = await db.execute(query)
        new_movie = result.scalars().first()

    return new_movie


@router.get(
    "/movies/{movie_id}/", response_model=MovieDetailSchema, responses={
        404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with the given ID was not found."
                    }
                }
            }
        }
    }
)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await crud.get_movie_by_id_with_join(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete(
    "/movies/{movie_id}/", status_code=204, responses={
        404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with the given ID was not found."
                    }
                }
            }
        }
    }
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await crud.get_movie_by_id(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await crud.delete_movie(db=db, movie_id=movie_id)
    return Response(content=None, status_code=204)


@router.patch(
    "/movies/{movie_id}/", responses={
        404: {
            "description": "Not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie with the given ID was not found."
                    }
                }
            }
        }
    }
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    movie = await crud.update_movie(
        db=db,
        movie_id=movie_id,
        movie_data=movie_data
    )

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return JSONResponse(
        status_code=200,
        content={"detail": "Movie updated successfully."}
    )
