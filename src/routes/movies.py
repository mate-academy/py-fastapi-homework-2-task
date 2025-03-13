from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import (
    MovieDetailSchema,
    MovieListResponseSchema,
    PaginationParams,
    MovieCreateRequestSchema,
    MovieUpdateSchema,
)
from crud import (
    create_movie_model,
    get_movie_model_by_name_and_date,
    get_movie_model,
    get_movies,
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))

    total_pages = (total_items + pagination.per_page - 1) // pagination.per_page

    if total_items == 0 or pagination.page > total_pages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    movies = await get_movies(pagination.offset, pagination.per_page, db)

    prev_page = (
        f"/theater/movies/?page={pagination.page - 1}&per_page={pagination.per_page}"
        if pagination.page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={pagination.page + 1}&per_page={pagination.per_page}"
        if pagination.page < total_pages else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def retrieve_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_model(movie_id, db=db)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    if await get_movie_model_by_name_and_date(movie_data.name, movie_data.date, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )
    try:
        new_movie = await create_movie_model(movie_data, db)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create movie due to integrity error. Please check the data."
        )
    return new_movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def destroy_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie = await get_movie_model(movie_id, db=db)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
    summary="Update specific fields of a movie",
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    movie = await get_movie_model(movie_id, db=db)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
