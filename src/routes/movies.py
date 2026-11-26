import math

from fastapi import APIRouter, status, HTTPException, Request

from crud.movies import (
    all_movies,
    movies_count,
    find_movie_by_name_and_date,
    create_movie_by_data,
    movie_by_id,
    delete_movie_model,
)
from database.dependencies.db import SessionDep
from database.pagination import PaginationHelper
from schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieCreate

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={404: {"description": "No movies found."}},
)
async def get_movies(db: SessionDep, pagination: PaginationHelper, request: Request):
    movies = await all_movies(
        db=db,
        skip=(pagination.page - 1) * pagination.per_page,
        limit=pagination.per_page,
    )

    if len(movies) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    total_movies = await movies_count(db=db)
    total_pages = math.ceil(total_movies / pagination.per_page)

    prev_page = None
    next_page = None

    if pagination.page - 1 > 0:
        prev_page = (
            request.url.path
            + f"?page={pagination.page - 1}&per_page={pagination.per_page}"
        )

    if pagination.page + 1 <= total_pages:
        next_page = (
            request.url.path
            + f"?page={pagination.page + 1}&per_page={pagination.per_page}"
        )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_movies,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201,
    responses={
        409: {"description": "A movie with the same name and date already exists."}
    },
)
async def create_movie(db: SessionDep, movie: MovieCreate):
    existed_movie = await find_movie_by_name_and_date(
        db=db, name=movie.name, date=movie.date
    )

    if existed_movie is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    movie = await create_movie_by_data(db=db, movie_data=movie)

    return movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={404: {"description": "Movie with the given ID was not found."}},
)
async def movie_details(db: SessionDep, movie_id: int):
    movie = await movie_by_id(db=db, movie_id=movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=204,
    responses={404: {"description": "Movie with the given ID was not found."}},
)
async def delete_movie(db: SessionDep, movie_id: int):
    movie = await movie_by_id(db=db, movie_id=movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await delete_movie_model(db=db, movie=movie)
