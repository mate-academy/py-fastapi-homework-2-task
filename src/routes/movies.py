from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailSchema

router = APIRouter()

NO_MOVIES_ERROR = "No movies found."
NO_MOVIE_ID_ERROR = "Movie with the given ID was not found."


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIES_ERROR}}
            },
        }
    },
)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1),
):
    total = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = ceil(total / per_page)

    if total == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail=NO_MOVIES_ERROR)

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    movies = result.scalars().all()

    url_ = "/theater/movies?page="
    next_page = (
        f"{url_}{page + 1}&per_page={per_page}" if page < total_pages else None
    )
    prev_page = f"{url_}{page - 1}&per_page={per_page}" if page > 1 else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total,
    )


async def _get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if movie is None:
        raise HTTPException(status_code=404, detail=NO_MOVIE_ID_ERROR)
    return movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIE_ID_ERROR}}
            }
        }
    },
)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await _get_movie_by_id(db, movie_id)
    return movie
