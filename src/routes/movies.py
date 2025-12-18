from typing import Dict
from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MovieModel
from schemas.movies import (
    MovieCreate,
    MovieDetailResponse,
    MovieListResponse,
    MovieUpdate
)
from crud.movies import (
    generate_pagination_links,
    get_movie_list,
    create_movie,
    get_single_movie,
    delete_movie,
    update_movie
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponse)
async def read_movie_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    movies = await get_movie_list(db=db, page=page, per_page=per_page)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )
    total_pages = (total_items + per_page - 1) // per_page
    pagination_links = generate_pagination_links(
        total_pages=total_pages,
        page=page,
        per_page=per_page
    )
    return {
        "movies": movies,
        "prev_page": pagination_links["prev_page"],
        "next_page": pagination_links["next_page"],
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", status_code=201)
async def create_movie_with_all_entity(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_db)
):
    created_movie = await create_movie(
        db=db, movie=movie
    )
    return created_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponse)
async def read_single_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_movie = await get_single_movie(
        db=db, movie_id=movie_id
    )
    return db_movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    await delete_movie(
        db=db, movie_id=movie_id
    )


@router.patch("/movies/{movie_id}/", status_code=200)
async def partial_update_movie(
    movie_id: int,
    movie_update: MovieUpdate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    result = await update_movie(
        db=db,
        movie_id=movie_id,
        movie_update=movie_update
    )
    return result
