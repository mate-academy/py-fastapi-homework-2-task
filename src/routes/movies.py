from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.crud import (
    create_movie,
    get_movie,
    get_movies,
    delete_movie,
    update_movie_partial,
)
from schemas import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema, MovieUpdateSchema,
)

router = APIRouter()


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_movie(movie: MovieCreateSchema,
                    db: AsyncSession = Depends(get_db)):
    new_movie = await create_movie(db, movie)
    return new_movie


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    movies = await get_movies(db)

    total_items = len(movies)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    start = (page - 1) * per_page
    end = start + per_page
    paginated_movies = movies[start:end]

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": paginated_movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")


@router.patch("/movies/{movie_id}/")
async def patch_movie(
        movie_id: int,
        movie_update: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    await update_movie_partial(db, movie_id, movie_update)
    return {"detail": "Movie updated successfully."}
