from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse

from crud.exceptions import ItemDoesNotExist, ItemAlreadyExist, InvalidDataError
from crud.movie import (
    get_movies,
    create_movie,
    read_movie_detail,
    delete_movie_by_id,
    update_movie_by_id,
)
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int,
) -> MovieModel:
    try:
        return await read_movie_detail(db=db, movie_id=movie_id)
    except ItemDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (minimum: 1)"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page (1-20)"),
) -> MovieListResponseSchema:
    try:
        return await get_movies(db=db, page=page, per_page=per_page)
    except ItemDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def create_a_movie(
    db: Annotated[AsyncSession, Depends(get_db)], movie_data: MovieCreateSchema
) -> MovieModel:
    try:
        return await create_movie(db=db, movie_data=movie_data)
    except ItemAlreadyExist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )
    except InvalidDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int,
) -> None:
    try:
        await delete_movie_by_id(db=db, movie_id=movie_id)
    except ItemDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_a_movie(
    db: Annotated[AsyncSession, Depends(get_db)],
    movie_id: int,
    movie_data: MovieUpdateSchema,
) -> JSONResponse:
    try:
        await update_movie_by_id(db=db, movie_id=movie_id, movie_data=movie_data)
        return JSONResponse(status_code=200, content={"detail": "Movie updated successfully."})
    except ItemDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
