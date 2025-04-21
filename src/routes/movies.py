from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.movies import (
    added_movie,
    edit_movie,
    fetch_movies,
    fetch_movie_by_id,
    fetch_movie_by_params,
    get_count_movies,
    remove_movie,
)
from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema
from schemas.movies import MovieAddedSchema, MovieUpdateSchema


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1),
        db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Retrieve a list of movies with pagination.

    :param page: The page number to retrieve (defaults to 1). Must be greater than or equal to 1.
    :param per_page: The number of movies to return per page (defaults to 10). Must be greater than or equal to 1.
    :param db: The asynchronous database session, injected via Depends.
    :return: A dictionary containing the list of movies, pagination details, and total counts.
    :raises HTTPException: If no movies are found or the requested page is out of range.
    """

    movies = await fetch_movies(session=db, offset=((page - 1) * per_page), limit=per_page)

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    count_movies = await get_count_movies(session=db)
    total_pages = (count_movies + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": count_movies,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieModel:
    """
    Retrieve a movie by its ID.

    :param movie_id: The ID of the movie to retrieve.
    :param db: The asynchronous database session, injected via Depends.
    :return: The movie data if found.
    :raises HTTPException: If the movie with the given ID does not exist.
    """
    movie = await fetch_movie_by_id(movie_id=movie_id, session=db)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_movie(
        movie_data: MovieAddedSchema,
        db: AsyncSession = Depends(get_db)
) -> MovieModel:
    """
    Create a new movie in the database.

    :param movie_data: The data for the movie to be created, passed as a MovieAddedSchema.
    :param db: The asynchronous database session, injected via Depends.
    :return: The details of the newly created movie as a MovieDetailResponseSchema.
    :raises HTTPException: If a movie with the same name and release date already exists (409 Conflict).
    """

    movie_db = await fetch_movie_by_params(
        {
            "name": movie_data.name,
            "date": movie_data.date,
        },
        session=db,
    )
    if movie_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    return await added_movie(movie_schema=movie_data, session=db)


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Update an existing movie in the database.

    :param movie_id: The ID of the movie to be updated.
    :param movie_data: The new data for the movie, passed as a MovieUpdateSchema.
    :param db: The asynchronous database session, injected via Depends.
    :return: A dictionary with a success message, indicating the movie was updated successfully.
    :raises HTTPException: If the movie with the given ID does not exist.
    """
    movie = await fetch_movie_by_id(movie_id=movie_id, session=db)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return await edit_movie(movie_id=movie_id, movie_schema=movie_data, session=db)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a movie from the database.

    :param movie_id: The ID of the movie to be deleted.
    :param db: The asynchronous database session, injected via Depends.
    :return: None, but raises a 404 error if the movie is not found.
    :raises HTTPException: If the movie with the given ID was not found (404 Not Found).
    """
    movie = await fetch_movie_by_id(movie_id=movie_id, session=db)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await remove_movie(movie_id=movie_id, session=db)
