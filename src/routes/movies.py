import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import MovieDetailSchema, MovieCreateSchema
from schemas.movies import MovieListResponseSchema, MovieUpdateSchema
from services.movies import (
    get_movie_by_id,
    get_movies,
    create_movie,
    delete_movie,
    update_movie,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def movie_list(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(
        default=10, ge=1, le=100, description="Items per page"
    ),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    movies, movies_count = await get_movies(db, page, per_page)

    if len(movies) == 0:
        raise HTTPException(404, detail="No movies found.")

    prev_page_num = page - 1
    if prev_page_num > 0:
        prev_page = (
            f"/theater/movies/?page={prev_page_num}&per_page={per_page}"
        )
    else:
        prev_page = None

    total_pages = math.ceil(movies_count / per_page)

    next_page_num = page + 1
    if next_page_num < total_pages:
        next_page = (
            f"/theater/movies/?page={next_page_num}&per_page={per_page}"
        )
    else:
        next_page = None

    return MovieListResponseSchema(
        movies=movies,
        total_items=movies_count,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def movie_details(
    movie_id: int, db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    movie = await get_movie_by_id(db, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def movie_create(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_movie(db, movie_data)

    except IntegrityError as e:
        await db.rollback()

        error_message = str(e.orig)

        if (
            "UNIQUE constraint failed" in error_message
            or "duplicate key" in error_message
        ):
            if (
                "movies.name" in error_message
                and "movies.date" in error_message
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"A movie with the name '{movie_data.name}' "
                        f"and release date '{movie_data.date}' "
                        f"already exists."
                    ),
                )

        raise HTTPException(
            status_code=400,
            detail="Database integrity error",
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the movie: {str(e)}",
        )


@router.delete("/movies/{movie_id}/", status_code=204)
async def movie_delete(movie_id: int, db: AsyncSession = Depends(get_db)):
    movies_deleted = await delete_movie(db, movie_id)

    if movies_deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )


@router.patch("/movies/{movie_id}/")
async def movie_update(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movies_updated = await update_movie(db, movie_id, movie_data)

    if movies_updated == 0:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return {
        "detail": "Movie updated successfully.",
    }
