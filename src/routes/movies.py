from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_all_movies, get_movie_by_id
from crud.movies import create_movie as create_movie_crud, delete_movie_by_id, update_movie_by_id
from database import get_db
from schemas import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema
from schemas.movies import MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    return await get_all_movies(db=db, page=page, per_page=per_page)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(film: MovieCreateSchema, db: AsyncSession = Depends(get_db),):
    movie = await create_movie_crud(db=db, film=film)
    return MovieDetailSchema.model_validate(movie).dict()


@router.get("/movies/{film_id}/", response_model=MovieDetailSchema)
async def get_film(film_id: int, db: AsyncSession = Depends(get_db)):
    return await get_movie_by_id(db=db, film_id=film_id)




@router.patch("/movies/{film_id}/")
async def update_movie(
        film_id: int,
        film: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)):
    return await update_movie_by_id(db=db, film_id=film_id, film=film)
