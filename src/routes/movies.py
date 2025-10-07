from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_movies, get_movie, get_or_create, delete_movie, update_movie, movie_create
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListSchema,
    MovieErrorSchema,
    MovieShortSchema,
    MovieCreateResponseSchema,
    MovieCreateRequestSchema,
    MovieDetailSchema,
    MovieUpdateResponseShema,
    MovieUpdateRequestSchema
)

router = APIRouter(prefix="/movies")


@router.get(
    "/",
    response_model=MovieListSchema,
    responses={
        404: {
            "model": MovieErrorSchema,
            "description": "No movies found."
        }
    }
)
async def movies_list(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    movies = await get_movies(db, page, per_page)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_path = "/theater/movies/"
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None
    return {
        "movies": [MovieShortSchema.model_validate(m) for m in movies],
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/",
    response_model=MovieCreateResponseSchema,
    status_code=201,
    responses={
        409: {
            "model": MovieErrorSchema,
            "description": "A movie with the same name and date already exists"
        }
    }
)
async def create_movie(
        movie: MovieCreateRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    movie_exist = await get_movie(db=db, name=movie.name, date=movie.date)

    if movie_exist:
        raise HTTPException(status_code=409, detail=f"A movie with the name '{movie.name}' "
                                                    f"and release date '{movie.date}' already exists.")

    new_movie = await movie_create(db, movie)
    created_movie = await get_movie(db=db, id=new_movie.id)

    return MovieCreateResponseSchema.model_validate(created_movie)


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "model": MovieErrorSchema,
            "description": "Movie with the given ID was not found."
        }
    }
)
async def movies_detail(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db=db, id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/{movie_id}/",
    status_code=204,
    responses={
        404: {
            "model": MovieErrorSchema,
            "description": "Movie with the given ID was not found."
        }
    }
)
async def remove_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await delete_movie(db, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return


@router.patch(
    "/{movie_id}/",
    response_model=MovieUpdateResponseShema,
    responses={
        400: {
            "model": MovieErrorSchema,
            "description": "Invalid input data."
        },
        404: {
            "model": MovieErrorSchema,
            "description": "Movie with the given ID was not found."
        }
    }
)
async def movie_update(
        movie_id: int,
        payload: MovieUpdateRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(db, id=movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        await update_movie(db, movie_id, payload.model_dump(exclude_none=True))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return MovieUpdateResponseShema.model_validate({
        "detail": "Movie updated successfully."
    })
