import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from crud.movies import get_paginated_movies_list, get_movie_by_id, get_movie_by_name_and_date
from database import get_db
from schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema, MoviePatchSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db_session: Annotated[AsyncSession, Depends(get_db)],
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    movies, count = await get_paginated_movies_list(db_session=db_session, page=page, per_page=per_page)
    if len(movies) == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    page_count = math.ceil(count / per_page)
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < page_count else None
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=page_count,
        total_items=count,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
        db_session: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int,
):
    movie_from_db = await get_movie_by_id(db_session=db_session, movie_id=movie_id)
    if movie_from_db is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie_from_db


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        db_session: Annotated[AsyncSession, Depends(get_db)],
        movie_data: MovieCreateSchema,
):
    movie_from_db = await get_movie_by_name_and_date(
        db_session=db_session,
        movie_name=movie_data.name,
        movie_date=movie_data.date
    )
    if movie_from_db is not None:
        raise HTTPException(409,
                            detail=f"A movie with the name '{movie_data.name}' "
                                   f"and release date '{movie_data.date}' "
                                   f"already exists.")

    return await crud.movies.create_movie(db_session=db_session, movie_data=movie_data)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        db_session: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int,
):
    movie_from_db = await get_movie_by_id(db_session=db_session, movie_id=movie_id)
    if movie_from_db is None:
        raise HTTPException(404, detail="Movie with the given ID was not found.")
    await db_session.delete(movie_from_db)
    await db_session.commit()


@router.patch("/movies/{movie_id}/")
async def patch_movie(
        db_session: Annotated[AsyncSession, Depends(get_db)],
        movie_id: int,
        movie_data: MoviePatchSchema,
):
    movie_from_db = await get_movie_by_id(db_session=db_session, movie_id=movie_id)
    if movie_from_db is None:
        raise HTTPException(404, detail="Movie with the given ID was not found.")
    try:
        await crud.movies.patch_movie(
            db_session=db_session,
            movie_id=movie_id,
            movie_data=movie_data,
        )
    except IntegrityError:
        raise HTTPException(400, detail="Invalid input data.")
    return {"detail": "Movie updated successfully."}
