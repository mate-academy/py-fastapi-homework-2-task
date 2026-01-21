from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.movies import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MessageSchema,
)
from src.crud.crud import (
    get_movies,
    get_movie_by_id,
    create_movie,
    update_movie,
    delete_movie,
)

movie_router = APIRouter(prefix="/movies", tags=["Movies"])


@movie_router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    data = await get_movies(db, page, per_page)

    prev_page = (
        f"{request.url.include_query_params(page=(page - 1), per_page=per_page)}"[18:] if page > 1 else None
    )
    next_page = (
        f"{request.url.include_query_params(page=(page + 1), per_page=per_page)}"[18:]
        if page < data["total_pages"]
        else None
    )

    return MovieListResponseSchema(
        movies=data["movies"],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=data["total_pages"],
        total_items=data["total_items"],
    )


@movie_router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_movie_by_id(db, movie_id)


@movie_router.post(
    "/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie_route(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await create_movie(db, movie_data)


@movie_router.patch("/{movie_id}/", response_model=MessageSchema)
async def update_movie_route(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    await update_movie(db, movie_id, movie_data)
    return MessageSchema(detail="Movie updated successfully.")


@movie_router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_route(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    await delete_movie(db, movie_id)
