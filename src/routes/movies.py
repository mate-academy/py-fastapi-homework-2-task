from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud.movies import (
    get_movie_by_id,
    get_list_movies,
    create_movie,
    delete_movie,
    update_movie,
)
from database import get_db
from schemas.movies import (
    PaginatedMoviesResponse,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieDetailSchema,
)

router = APIRouter()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    movie = await get_movie_by_id(movie_id, db)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.get("/movies/", response_model=PaginatedMoviesResponse)
async def list_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    if page < 1 or per_page < 1 or per_page > 20:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    movies, total_items, total_pages = await get_list_movies(db, page, per_page)

    base_path = "/theater/movies/"

    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_path}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return PaginatedMoviesResponse(
        movies=movies,
        total_pages=total_pages,
        total_items=total_items,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_new_movie(
    movie: MovieCreateSchema, db: Annotated[AsyncSession, Depends(get_db)]
):
    new_movie = await create_movie(db, movie)
    return new_movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_by_id(
    movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    await delete_movie(db, movie_id)  # Noqa
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie_by_id(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    movie_for_update = await update_movie(db, movie_id, movie)
    return movie_for_update
