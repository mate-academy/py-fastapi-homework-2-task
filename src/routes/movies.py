import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status


from crud import movies as crud
from crud.movies import get_movie_by_id
from database import get_db
from schemas import MovieListResponseSchema, MovieCreateSchema, MovieDetailSchema
from schemas.movies import MovieUpdateSchema

router = APIRouter()


async def check_exists_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(db=db, movie_id=movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
    db: AsyncSession = Depends(get_db),
):
    movies = await crud.get_all_movies(db=db, page=page, per_page=per_page)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    count = await crud.get_count_movies(db=db)

    total_pages = math.ceil(count / per_page)

    response = {
        "movies": movies,
        "prev_page": (
            None
            if page == 1
            else f"/theater/movies/?page={page - 1}&per_page={per_page}"
        ),
        "next_page": (
            None
            if page >= total_pages
            else f"/theater/movies/?page={page + 1}&per_page={per_page}"
        ),
        "total_pages": total_pages,
        "total_items": count,
    }

    return response


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    db_movie = await crud.get_movie_by_name_and_date(
        db=db, name=movie.name, date=movie.date
    )

    if db_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{db_movie.name}' and release date '{db_movie.date}' already exists.",
        )

    return await crud.create_movie(db=db, movie=movie)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await check_exists_movie(db=db, movie_id=movie_id)

    await db.refresh(movie, ["genres", "actors", "languages", "country"])

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    await check_exists_movie(db=db, movie_id=movie_id)
    await crud.delete_movie(db=db, movie_id=movie_id)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):

    await check_exists_movie(db=db, movie_id=movie_id)
    await crud.update_movie(db=db, movie_id=movie_id, movie=movie)

    return {"detail": "Movie updated successfully."}
