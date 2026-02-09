import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import schemas.movies as schemas
from crud.movies import (
    get_movie_by_id,
    delete_movie,
    get_movies_list,
    patch_movie,
    create_movie,
)
from database import get_db, MovieModel

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_all_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):

    skip = (page - 1) * per_page
    limit = per_page

    movies_list = await get_movies_list(db=db, skip=skip, limit=limit)
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page == total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/", response_model=schemas.MovieCreateResponseSchema, status_code=201
)
async def create_movie_endpoint(
    movie: schemas.MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await create_movie(movie=movie, db=db)


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await get_movie_by_id(db=db, movie_id=movie_id)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_endpoint(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(movie_id=movie_id, db=db)
    await delete_movie(movie=movie, db=db)


@router.patch(
    "/movies/{movie_id}/",
    status_code=200,
)
async def patch_movie_endpoint(
    movie_id: int,
    movie: schemas.MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    db_movie = await get_movie_by_id(movie_id=movie_id, db=db)
    await patch_movie(db_movie=db_movie, movie=movie, db=db)
    return {"detail": "Movie updated successfully."}
