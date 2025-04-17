from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.params import Depends
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema
from crud import movies as crud
from schemas.movies import MovieCreateSchema

router = APIRouter()


@router.get(
    "/movies/", response_model=MovieListResponseSchema, responses={
        404: {
            "description": "No movies found.",
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."}
                }
            }
        }
    }
)
async def get_movies(
    page: Annotated[
        int, Query(ge=1, description="The page number to fetch")
    ] = 1,
    per_page: Annotated[
        int, Query(
            ge=1, le=20, description="Number of movies to fetch per page"
        )
    ] = 10,
    db: AsyncSession = Depends(get_db)
):
    movies, total_items = await crud.get_movies(
        db=db, page=page, per_page=per_page
    )
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail=f"No movies found for the specified page."
        )

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }
