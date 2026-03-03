from math import ceil
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from crud import movies_crud
from database import get_db, MovieModel
from schemas.movies import (MovieListResponseSchema, MovieResponseSchema, MovieCreateSchema, MovieDetailSchema,
                            MovieUpdateSchema)

router = APIRouter(prefix="/movies")


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(request: Request,
                     page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=20),
                     db: AsyncSession = Depends(get_db)):

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = max(ceil(total_items / per_page), 1)

    result = await db.execute(
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies_data = [MovieResponseSchema.model_validate(m) for m in movies]

    def make_page_url(page_number: int) -> str | None:
        if 1 <= page_number <= total_pages:
            base_url = request.url.path.replace('/api/v1', '')
            query_param = urlencode({'page' : page_number, 'per_page': per_page})
            return f"{base_url}?{query_param}"
        return None

    return MovieListResponseSchema(
        movies=movies_data,
        prev_page=make_page_url(page - 1),
        next_page=make_page_url(page + 1),
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    return await movies_crud.create_movie(movie, db)


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.actors),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country)
        ).where(MovieModel.id == movie_id)
    )

    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/", status_code=status.HTTP_200_OK, description="Movie updated successfully.")
async def update_movie(movie_id: int, movie_request: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(
            MovieModel.id == movie_id
        )
    )
    movie_db = result.scalars().first()

    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_request.model_dump(exclude_unset=True)

    if not update_data:
        return {"detail": "Movie updated successfully."}

    for field_name, field_value in update_data.items():
        setattr(movie_db, field_name, field_value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
