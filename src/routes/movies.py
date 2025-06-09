from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from crud import (
    delete_movie,
    post_movie,
    read_movie,
    update_movie,
)
from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema
from schemas.movies import MovieListResponseSchema, MovieUpdateSchema, MovieCreateSchema, MovieCreateResponse, \
    MessageResponse
from schemas.movies import MovieBaseSchema


router = APIRouter()
route_prefix = "/theater/movies"


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await read_movie(movie_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    status = await delete_movie(movie_id, db)
    if not status:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return


@router.patch("/movies/{movie_id}/", response_model=MessageResponse)
async def patch_movie(movie_id: int, movie_update: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await update_movie(movie_id, movie_update, db)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return {"detail": "Movie updated successfully."}


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(func.count(MovieModel.id)))
    result_count = result.scalar_one()

    if result_count == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Pagination

    total_pages = (result_count + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page number exceeds total pages.")

    skip_results = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).offset(skip_results).limit(per_page)
        .order_by(MovieModel.id.desc())
    )

    movies = result.scalars().all()

    prev_page = (
        f"{route_prefix}/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"{route_prefix}/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=[MovieBaseSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=result_count
    )


@router.post("/movies/", response_model=MovieCreateResponse, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    new_movie = await post_movie(movie, db)
    return new_movie
