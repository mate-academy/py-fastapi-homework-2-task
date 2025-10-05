from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from repository import get_movies, get_number_of_movies
from schemas import MovieListResponseSchema, MovieNotFoundSchema

router = APIRouter(prefix="/movies")


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "model": MovieNotFoundSchema,
            "description": "No movies found."
        }
    }
)
async def list_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    movies = await get_movies(db, per_page, page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await get_number_of_movies(db)
    total_pages = (total_items - 1) // per_page + 1
    prev_page = str(request.url.replace_query_params(page=page - 1, per_page=per_page)) if page > 1 else None
    next_page = str(request.url.replace_query_params(page=page + 1, per_page=per_page)) if page < total_pages else None

    return MovieListResponseSchema.model_validate(
        {
            "movies": movies,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total_items,
        }
    )

