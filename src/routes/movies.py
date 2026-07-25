from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_db
from database.crud import movies as crud_movies
from schemas import MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema

router = APIRouter(prefix="/movies")


@router.get("/")
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    movies, total_items = await crud_movies.get_all_movies(session=db, page=page, per_page=per_page)
    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/")
async def add_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    try:
        movie = await crud_movies.create_movie(session=db, movie_data=movie_data)
    except crud_movies.MovieAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return MovieDetailSchema.model_validate(movie)


@router.get("/{movie_id}/")
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    movie = await crud_movies.get_movie_by_id(session=db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return MovieDetailSchema.model_validate(movie)


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> None:
    is_deleted = await crud_movies.delete_movie(session=db, movie_id=movie_id)
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
