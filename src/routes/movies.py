import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database import MovieModel
from repositories.movies import MovieRepository, get_movie_repository
from schemas import (
    HTTP404ErrorSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTP404ErrorSchema,
            "content": {
                "application/json": {
                    "example": HTTP404ErrorSchema(detail="No movies found."),
                },
            },
        },
    },
)
async def get_movies(
    movie_repo: Annotated[MovieRepository, Depends(get_movie_repository)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
) -> MovieListResponseSchema:
    total_items = await movie_repo.get_total()
    total_pages = math.ceil(total_items / per_page)
    if not total_items or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    movies = await movie_repo.get_objects_or_404(
        offset=(page - 1) * per_page,
        limit=per_page,
        ordering=MovieModel.id.desc(),
    )
    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(movie) for movie in movies],
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTP404ErrorSchema,
            "content": {
                "application/json": {
                    "example": HTTP404ErrorSchema(
                        detail="Movie with the given ID was not found.",
                    ),
                },
            },
        },
    },
)
async def get_movie_by_id(
    movie_id: int,
    movie_repo: Annotated[MovieRepository, Depends(get_movie_repository)],
) -> MovieDetailSchema:
    movie = await movie_repo.get_object_or_404(MovieModel.id == movie_id)
    return MovieDetailSchema.model_validate(movie)


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Movie with the same name and date already exists.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid input data.",
        },
    },
)
async def create_movie(
    movie_data: MovieCreateSchema,
    movie_repo: Annotated[MovieRepository, Depends(get_movie_repository)],
) -> MovieDetailSchema:
    if await movie_repo.is_exist(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )
    movie = await movie_repo.create_object(movie_data)
    movie = await movie_repo.get_object(MovieModel.id == movie.id)
    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."},
                },
            },
        },
    },
)
async def delete_movie(
    movie_id: int,
    movie_repo: Annotated[MovieRepository, Depends(get_movie_repository)],
) -> None:
    await movie_repo.delete_object(MovieModel.id == movie_id, raise_exception=True)
    return None


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie updated successfully."}
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Movie with the given ID was not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid input data.",
            "content": {
                "application/json": {"example": {"detail": "Invalid input data."}}
            },
        },
    },
)
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    movie_repo: Annotated[MovieRepository, Depends(get_movie_repository)],
):
    await movie_repo.update_object(
        MovieModel.id == movie_id,
        data=payload.model_dump(exclude_unset=True),
        raise_exception=True,
    )

    return {"detail": "Movie updated successfully."}
