from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud.movies import (
    create_movie,
    get_movie_by_id,
    get_movies,
    update_movie,
)
from database import MovieModel, get_db
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_all_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    movies = await get_movies(db, per_page, page)
    count_result = await db.execute(select(func.count()).select_from(MovieModel))
    count = count_result.scalar()
    page_count = (count + per_page - 1) // per_page

    prev_page = (
        None if page <= 1 else f"/theater/movies/?page={page - 1}&per_page={per_page}"
    )
    next_page = (
        None
        if page >= page_count
        else f"/theater/movies/?page={page + 1}&per_page={per_page}"
    )

    return MovieListResponseSchema.model_validate(
        {
            "movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": page_count,
            "total_items": count,
        }
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema, status_code=200)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await get_movie_by_id(db, movie_id)
    if not result:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return result


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await get_movie_by_id(db, movie_id)
    if not result:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(result)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create(
    movie: MovieCreateSchema, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await create_movie(movie, db)
    return result


@router.patch("/movies/{movie_id}/", response_model=dict, status_code=200)
async def update(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await update_movie(movie_id, movie, db)
    return result
