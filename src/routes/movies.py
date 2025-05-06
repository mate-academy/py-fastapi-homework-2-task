from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from crud.movies import (
    get_paginated_movies,
    get_movies_count,
    build_page_url,
    create_new_movie,
    delete_movie,
    get_movie_data,
    patch_movie,
)
from database import get_db
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter()

@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movie_list(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    skip = (page - 1) * per_page
    movies = await get_paginated_movies(db=db, offset=skip, limit=per_page)
    if not movies:
        # this logic is specified in the task, it is not an error!
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    total_items = await get_movies_count(db=db)
    total_pages = (total_items + per_page - 1) // per_page
    prev_url = (
        build_page_url(page_num=page - 1, per_page=per_page)
        if page > 1
        else None
    )
    next_url = (
        build_page_url(page_num=page + 1, per_page=per_page)
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_url,
        next_page=next_url,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie_to_create: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    movie = await create_new_movie(movie=movie_to_create, db=db)
    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_data(db=db, movie_id=movie_id)
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    return await delete_movie(db=db, movie_id=movie_id)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    patch_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    return await patch_movie(db=db, movie_id=movie_id, movie_data=patch_data)
