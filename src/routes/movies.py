from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import get_db, MovieModel
from database.crud.movies import get_all_movies
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieListItemSchema

router = APIRouter(prefix="/movies")


@router.get("/")
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    movies, total_items = await get_all_movies(session=db, page=page, per_page=per_page)
    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )
