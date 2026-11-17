from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from database.session_sqlite import AsyncSQLiteSessionLocal
from pagination.utils import paginate
from schemas.movies import MovieListObjectResponse, MovieListResponseSchema, MovieCreateSchema, MovieCreateResponseSchema

from crud.movies import create_movie

router = APIRouter()

@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSQLiteSessionLocal = Depends(get_db)
):
    (
        movies,
        total_items,
        total_pages,
        prev_page,
        next_page
    ) = await paginate(
        db,
        MovieModel,
        request,
        page,
        per_page
    )

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
        movies=[MovieListObjectResponse.model_validate(movie) for movie in movies],
    )


@router.post("/movies/", response_model=MovieCreateResponseSchema)
async def create_new_movie(
    movie: MovieCreateSchema,
    db: AsyncSQLiteSessionLocal = Depends(get_db),
):
    return await create_movie(movie, db)