from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from crud import (
    get_all_movies,
    get_movies_count,
    get_movie_by_name_and_date,
    create_movie_model,
    get_movie_by_id_relations,
    delete_movie_by_id,
    update_movie_model
)
from database import get_db

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_movies(db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=20)):
    movies = await get_all_movies(db=db, start=(page - 1) * per_page, count=per_page)
    total_items = await get_movies_count(db)
    total_pages = ceil(total_items / per_page)

    base_url = router.url_path_for("get_movies")

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    next_page = None
    prev_page = None

    if page > 1:
        prev_page = f"/theater{base_url}?page={page - 1}&per_page={per_page}"

    if page < total_pages:
        next_page = f"/theater{base_url}?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=schemas.MovieDetailSchema, status_code=201)
async def create_movie(movie: schemas.MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    name = movie.name
    date = movie.date
    exists = await get_movie_by_name_and_date(db=db, name=name, date=date)
    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{name}' and release date '{exists.date}' already exists.")
    movie = await create_movie_model(db=db, movie_data=movie)
    return movie


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id_relations(db=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.patch("/movies/{movie_id}/")
async def edit_movie(movie_id: int, movie: schemas.MovieEditSchema, db: AsyncSession = Depends(get_db)):
    is_updated = await update_movie_model(db=db, movie_id=movie_id, movie=movie)
    if not is_updated:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_movie_by_id(db=db, movie_id=movie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
