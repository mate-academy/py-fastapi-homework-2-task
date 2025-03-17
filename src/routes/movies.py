import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response, JSONResponse

from crud import get_movies, check_movie_exists, create_movie, get_movie, delete_movie, update_movie
from database import get_db
from schemas import MovieListResponseSchema
from schemas.movies import MovieCreateSchema, MovieDetailSchema, MovieUpdateSchema
from schemas.pagination import PaginationParams


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_list(
    pagination: Annotated[PaginationParams, Query()],
    db: AsyncSession = Depends(get_db),
):
    offset_min = (pagination.page - 1) * pagination.per_page
    offset_max = pagination.page * pagination.per_page
    movies = await get_movies(db)
    paginated_result = movies[offset_min:offset_max]
    if not paginated_result:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_pages = math.ceil(len(movies) / pagination.per_page)
    return {
        "movies": paginated_result,
        "prev_page": (
            "/theater/movies/" + f"?page={pagination.page - 1}&per_page={pagination.per_page}"
            if pagination.page > 1 else None
        ),
        "next_page": (
            "/theater/movies/" + f"?page={pagination.page + 1}&per_page={pagination.per_page}"
            if pagination.page < total_pages else None
        ),
        "total_pages": total_pages,
        "total_items": len(movies),
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def movie_create(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    if await check_movie_exists(db, name=movie.name, date=movie.date):
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )
    new_film = await create_movie(db, movie)
    return new_film


@router.get("/movies/{movie_id}/")
async def retrieve_movie(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/")
async def movie_delete(movie_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    movie = await delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return Response(status_code=204)


@router.patch("/movies/{movie_id}/")
async def movie_partial_update(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> Response:
    update_data = movie.model_dump(exclude_unset=True)
    movie = await update_movie(db, movie_id, update_data)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return JSONResponse(status_code=200, content={"detail": "Movie updated successfully."})
