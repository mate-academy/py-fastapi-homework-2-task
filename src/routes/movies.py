from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from crud.movies import count_movies, get_movies_list, create_movie, get_detail_movie, delete_movie, update_movie
from database import get_db
from schemas.movies import (
    MoviesListResponse,
    MovieShortInfo,
    MovieDetailInfo,
    MovieCreateRequest, MovieUpdateRequest,
)

router = APIRouter()


@router.get("/movies/", response_model=MoviesListResponse)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page

    total_items = await count_movies(db)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = await get_movies_list(db, offset=offset, limit=per_page)

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page exceeds maximum number of pages.")

    base_url = "/theater/movies/"
    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"{base_url}?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"{base_url}?page={page + 1}&per_page={per_page}"

    return MoviesListResponse(
        movies=[
            MovieShortInfo(
                id=movie.id,
                name=movie.name,
                date=movie.date,
                score=movie.score,
                overview=movie.overview
            ) for movie in movies
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailInfo)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_detail_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.post("/movies/", response_model=MovieDetailInfo, status_code=201)
async def add_movie(
        movie_data: MovieCreateRequest,
        db: AsyncSession = Depends(get_db)
):
    try:
        new_movie = await create_movie(db, movie_data)
        return MovieDetailInfo.model_validate(new_movie, from_attributes=True)
    except HTTPException as e:
        raise e
    except Exception as e:
        error_details = {
            "error_type": str(type(e)),
            "error_message": str(e),
        }
        raise HTTPException(status_code=400, detail=f"Invalid input data. Details: {error_details}")


@router.delete("/movies/{movie_id}/", status_code=204)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    await delete_movie(db, movie_id)


@router.patch("/movies/{movie_id}/")
async def patch_movie(
    movie_id: int,
    data: MovieUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    return await update_movie(db, movie_id, data)
