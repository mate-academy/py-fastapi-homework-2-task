from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud.movies import get_paginated_movies, get_movies_count, build_page_url
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    skip = (page - 1) * per_page
    movies = await get_paginated_movies(db=db, offset=skip, limit=per_page)
    if not movies:
        # this logic is specified in the task, it is not an error!
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await get_movies_count(db=db)
    total_pages = (total_items + per_page - 1) // per_page
    prev_url = build_page_url(page_num=page - 1, per_page=per_page) if page > 1 else None
    next_url = build_page_url(page_num=page + 1, per_page=per_page) if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_url,
        next_page=next_url,
        total_pages=total_pages,
        total_items=total_items,
    )
