from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

from schemas.movies import (
    MovieCreate, 
    MovieUpdate, 
    MovieDetailSchema, 
    MovieListResponseSchema
)
from crud import (
    create_movie, 
    get_movie, 
    get_movies, 
    get_movies_count, 
    update_movie, 
    delete_movie,
    check_movie_exists
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * per_page
    movies = await get_movies(db, skip=skip, limit=per_page)
    total_items = await get_movies_count(db)
    total_pages = (total_items + per_page - 1) // per_page

    if not movies and total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    if page > total_pages > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = None
    next_page = None
    
    if page > 1:
        prev_page = f"/theater/movies/?page={page-1}&per_page={per_page}"
    
    if page < total_pages:
        next_page = f"/theater/movies/?page={page+1}&per_page={per_page}"
    
    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie_endpoint(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_db)
):
    if await check_movie_exists(db, movie.name, movie.date):
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )
    
    try:
        new_movie = await create_movie(db, movie)
        return new_movie
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.patch("/movies/{movie_id}/")
async def update_movie_endpoint(
    movie_id: int,
    movie: MovieUpdate,
    db: AsyncSession = Depends(get_db)
):
    existing_movie = await get_movie(db, movie_id)
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    
    try:
        await update_movie(db, movie_id, movie)
        return {"detail": "Movie updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_endpoint(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie = await delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return None
