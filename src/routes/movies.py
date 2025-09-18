from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi_pagination import Page, add_pagination, paginate

from pagination import CustomParams
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieListItemSchema
)
from crud import create_movie, update_movie, delete_movie_crud

from src.schemas.movies import MovieListItemSchema

router = APIRouter()


@router.get("/movies/",
            response_model=MovieListResponseSchema,
            responses = {
            404: {
            "description": "No movies found.",
            "content": {
                "application/json": {"example": {"detail": "No movies found."}}
            },
        }
    },
)
async def list_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    offset = (page - 1) * per_page
    count_movies = select(func.count(MovieModel.id))
    total_items = await db.scalar(count_movies)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    order_by = MovieModel.default_order_by()
    stmt = select(MovieModel)
    if order_by:
        stmt =stmt.order_by(*order_by)
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages and total_items > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    response = MovieListResponseSchema(movies=movie_list,
                                       prev_page=(
                                           f"/theater/movies/?page={page - 1}&per_page={per_page}"
                                           if page > 1
                                           else None
                                       ),
                                       next_page=(
                                           f"/theater/movies/?page={page + 1}&per_page={per_page}"
                                           if page < total_pages
                                           else None
                                       ),
                                       total_pages=total_pages,
                                       total_items=total_items)
    return response

@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema, status_code=200)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        ).where(MovieModel.id == movie_id)
    )

    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return MovieDetailSchema.model_validate(movie)



@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    new_movie = await create_movie(db, movie)
    return new_movie


@router.patch("/movies/{movie_id}/")
async def edit_movie(
    movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    await update_movie(db, movie_id, movie)

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    deleted_movie = await delete_movie_crud(db, movie_id)
    if not deleted_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
