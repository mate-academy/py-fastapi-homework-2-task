from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud.movies import (
    get_movie,
    get_movies,
    create_movie,
    update_movie,
    delete_movie
)
from database import get_db

from schemas import (
    MovieDetailSchema,
    MovieListResponseSchema
)
from schemas.movies import MovieCreate, MovieUpdate, MoviePatch

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_handler(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
):
    result = await get_movies(
        request=request,
        db=db,
        page=page,
        per_page=per_page
    )
    return result


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_handler(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(movie_id, db)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie_handler(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_db)
):
    new_movie = await create_movie(movie=movie, db=db)
    return new_movie


@router.put("/movies/{movie_id}/", response_model=None)
async def update_movie_handler(
        movie_id: int,
        updated_movie: MovieUpdate,
        db: AsyncSession = Depends(get_db),
):
    movie = await update_movie(movie_id=movie_id, updated_movie=updated_movie, db=db)
    return movie


@router.patch("/movies/{movie_id}/", response_model=None)
async def patch_movie_handler(
        movie_id: int,
        updated_movie: MoviePatch,
        db: AsyncSession = Depends(get_db),
):
    movie = await update_movie(movie_id=movie_id, updated_movie=updated_movie, db=db)
    return movie


@router.delete("/movies/{movie_id}/", response_model=None)
async def delete_movie_handler(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    await delete_movie(movie_id=movie_id, db=db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
