from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from crud.movies import get_all_movies, delete_movie_by_id, get_movie_by_id, create_movie_model, \
    get_movie_by_name_and_date, update_movie_by_id
from schemas.movies import MovieListResponseSchema, MovieRead, MovieCreate, MovieDetailSchema, MovieUpdateSchema
from database import get_db


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_endpoint(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1, description="Page number, >= 1"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page, 1-20"),
):

    movies = await get_all_movies(db, page, per_page)

    if len(movies.get("movies")) == 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    if page > movies.get("total_pages"):
        raise HTTPException(
            status_code=404,
            detail="Page number out of range."
        )

    return movies


@router.post("/movies/", response_model=MovieRead, status_code=201)
async def create_movie_endpoint(movie: MovieCreate, db: AsyncSession = Depends(get_db)):

    name = movie.name
    date = movie.date
    exists = await get_movie_by_name_and_date(db=db, name=name, date=date)

    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{name}' and release date '{exists.date}' already exists.")
    movie = await create_movie_model(db=db, movie_data=movie)
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_endpoint(
        movie_id: PositiveInt,
        db: AsyncSession = Depends(get_db),
):
    return await delete_movie_by_id(movie_id, db)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_endpoint(
        movie_id: PositiveInt,
        db: AsyncSession = Depends(get_db),
):
    movie = await get_movie_by_id(movie_id, db)

    return movie


@router.patch("/movies/{movie_id}/",
              status_code=200)
async def update_movie_endpoint(
        movie_id: PositiveInt,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):

    updated_movie = await update_movie_by_id(movie_id, movie_data, db)

    if updated_movie:
        return JSONResponse(
            status_code=200,
            content={"detail": "Movie updated successfully."}
        )
