import math
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import crud
import schemas
from database import get_db
from schemas import MovieListResponseSchema, MovieListItemSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    offset = (page - 1) * per_page
    movies, total_items = await crud.movie_service.get_movies_paginated(db=db, limit=per_page, offset=offset)
    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    base_path = request.url.path
    if base_path.startswith("/api/v1"):
        base_path = base_path[len("/api/v1") :]
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None
    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieListItemSchema)
async def get_movie_by_id(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    movie = await crud.movie_service.get_movie_by_id(db=db, movie_id=movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", status_code=status.HTTP_201_CREATED, response_model=MovieListItemSchema)
async def create_movie(movie_data: schemas.MovieDetailSchema, db: Annotated[AsyncSession, Depends(get_db)]):
    movie = await crud.movie_service.create_movie(db=db, movie_data=movie_data)
    return movie


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int, movie_data: schemas.MovieUpdateSchema, db: Annotated[AsyncSession, Depends(get_db)]
):
    await crud.movie_service.update_movie(db=db, movie_id=movie_id, movie_data=movie_data)
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    await crud.movie_service.delete_movie(db=db, movie_id=movie_id)
