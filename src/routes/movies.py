from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
    MovieListResponseSchema,

router = APIRouter()

# Write your code here

@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1, description="Page number (>=1)"),
        per_page: int = Query(10, ge=1, le=20, description="Number of movies per page (1-20)"),
        db: AsyncSession = Depends(get_db)
):
    total_count = await db.execute(select(MovieModel))
    total_items = len(total_count.scalars().all())

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    query = select(MovieModel).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    prev_page = f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }

