from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db


from schemas.movies import (
    FilmCreate, FilmRead, FilmUpdate, PaginatedFilmList, MovieListItemSchema
)
from crud import (
    create_film,
    get_film_by_id,
    delete_film,
    update_film,
    get_paginated_movies
)

router = APIRouter()


@router.get("/movies/", response_model=PaginatedFilmList)
async def list_movies(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    movies, total_items, total_pages = await get_paginated_movies(db, page, per_page)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_schemas = [MovieListItemSchema.model_validate(m, from_attributes=True) for m in movies]
    path = "/theater/movies/"
    prev_page = f"{path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{path}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return PaginatedFilmList(
        movies=movie_schemas,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=FilmRead, status_code=201)
async def create_movie(film: FilmCreate, db: AsyncSession = Depends(get_db)):
    movie = await create_film(db, film)
    return FilmRead.model_validate(movie, from_attributes=True)


@router.get("/movies/{movie_id}/", response_model=FilmRead)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_film_by_id(db, movie_id)
    return FilmRead.model_validate(movie, from_attributes=True)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    await delete_film(db, movie_id)


@router.patch("/movies/{movie_id}/", status_code=200)
async def patch_movie(movie_id: int, update: FilmUpdate, db: AsyncSession = Depends(get_db)):
    await update_film(db, movie_id, update)
    return {"detail": "Movie updated successfully."}
