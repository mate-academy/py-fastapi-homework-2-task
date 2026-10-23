from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.crud.crud import (
    create_movie,
    update_movie,
    delete_movie,
    DuplicateMovieError,
)
from src.database import get_db, MovieModel
from src.schemas import MovieListResponseSchema
from src.schemas.movies import (
    MovieReadSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieListItemSchema
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def list_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
):
    total_items_result = await db.execute(
        select(func.count(MovieModel.id))
    )
    total_items = total_items_result.scalar_one() or 0

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    movie_list = [
        MovieListItemSchema.model_validate(movie)
        for movie in movies
    ]

    base_url = "/theater/movies/"

    prev_page = (
        f"{base_url}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movie_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_items": total_items,
        "total_pages": total_pages,
    }


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieReadSchema
)
async def read_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            joinedload(MovieModel.country),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    try:
        new_movie = await create_movie(db, movie)
        return new_movie
    except DuplicateMovieError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/movies/{movie_id}/")
async def edit_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        updated_movie = await update_movie(db, movie_id, movie)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    if updated_movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return {"detail": "Movie updated successfully."}


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    deleted_movie = await delete_movie(db, movie_id)

    if deleted_movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
