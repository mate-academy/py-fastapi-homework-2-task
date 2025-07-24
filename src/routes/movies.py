from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieCreateResponseSchema,
    MovieUpdateSchema,
)
from services.crud import (
    create_film,
    delete_movie,
    get_movies,
    get_movie_with_id,
    update_movie,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
):
    movies = await get_movies(request=request, db=db, page=page, per_page=per_page)
    return movies


@router.post(
    "/movies/",
    response_model=MovieCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movies(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    result = await create_film(db=db, movie_data=movie_data)
    return result


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_with_id(movie_id=movie_id, db=db)
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_endpoint(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await delete_movie(db, movie_id)


@router.patch("/movies/{movie_id}/", response_model=MovieUpdateSchema)
async def update_movie_endpoint(
    movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    await update_movie(movie_id=movie_id, db=db, movie=movie_data)
    return JSONResponse(
        content={"detail": "Movie updated successfully."}, status_code=200
    )
