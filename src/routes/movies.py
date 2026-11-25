import math

from fastapi import APIRouter, status, HTTPException, Request

from crud.movies import all_movies, movies_count
from database.dependencies.db import SessionDep
from database.pagination import PaginationHelper
from schemas.movies import MovieListResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
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
