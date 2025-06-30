from fastapi import APIRouter, Response, Path, Depends, status, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import (
    MovieCreateSchema,
    MovieResponseSchema,
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema, MovieUpdateSchema
)
from src.database.session_postgresql import get_postgresql_db as get_async_session
from src.crud.movies import create_movie, get_movies, get_movie_by_id, delete_movie, update_movie

from src.database import get_db, MovieModel
from src.database.models import CountryModel, GenreModel, ActorModel, LanguageModel


router = APIRouter()

@router.post(
    "/movies/",
    response_model=MovieResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie_view(
    movie_data: MovieCreateSchema,
    session: AsyncSession = Depends(get_async_session)
):

    movie = await create_movie(session, movie_data)
    return movie

@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK
)
async def get_movies_view(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    skip = (page - 1) * size
    movies, total = await get_movies(session, skip=skip, limit=size)

    return MovieListResponseSchema(
        total=total,
        page=page,
        size=size,
        items=movies
    )


@router.get(
    "/movies/{movie_id}",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_200_OK
)
async def get_movie_detail(
    movie_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_async_session)
):
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@router.patch(
    "/movies/{movie_id}",
    response_model=MovieResponseSchema,
    status_code=status.HTTP_200_OK
)
async def patch_movie(
    movie_id: int = Path(..., ge=1),
    movie_data: MovieUpdateSchema = Body(...),
    session: AsyncSession = Depends(get_async_session)
):
    movie = await update_movie(session, movie_id, movie_data)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.delete(
    "/movies/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie_view(
    movie_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_async_session)
):
    success = await delete_movie(session, movie_id)
    if not success:
        raise HTTPException(status_code=404, detail="Movie not found")
    return Response(status_code=204)
