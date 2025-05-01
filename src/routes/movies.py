from math import ceil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema
from schemas.movies import MovieListItemSchema

router = APIRouter()

NO_MOVIES_ERROR = "No movies found."

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