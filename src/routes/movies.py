from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MovieModel
from schemas import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MoviePatchSchema,
)
from crud.movies import (
    get_movies,
    create_movie,
    get_movie_by_id,
    delete_movie,
    patch_movie,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    offset = (page - 1) * per_page

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page

    if total_items == 0 or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    base_url = "/theater/movies"
    prev_page = f"{base_url}/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_url}/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    movies = await get_movies(db, offset=offset, limit=per_page)

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def add_movie(movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    return await create_movie(db, movie_data)


@router.patch("/movies/{movie_id}/")
async def update_movie_partial(
    movie_id: int, data: MoviePatchSchema, db: AsyncSession = Depends(get_db)
):
    await patch_movie(db, movie_id, data)
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
