from fastapi import APIRouter, status

from dependencies.movies import DbAsyncDep
from routes import crud
from schemas import MovieListItemSchema
from schemas.movies import MovieInputCreateSchema, MovieOutputCreateSchema, MovieRetrieveSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListItemSchema)
async def read_movies(db: DbAsyncDep, page: int = 1, per_page: int = 10):
    result = await crud.read_movies(db=db, page=page, per_page=per_page)
    return result


@router.get("/movies/{movie_id}/", response_model=MovieRetrieveSchema)
async def read_movie(movie_id: int, db: DbAsyncDep):
    result = await crud.read_movie(movie_id=movie_id, db=db)
    return result


@router.post("/movies/", response_model=MovieOutputCreateSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_schema: MovieInputCreateSchema, db: DbAsyncDep):
    result = await crud.create_movie(movie_schema=movie_schema, db=db)
    return result


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: DbAsyncDep):
    result = await crud.delete_movie(movie_id=movie_id, db=db)
    return result


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie_update_fields: MovieUpdateSchema, db: DbAsyncDep):
    result = await crud.update_movie(movie_update_fields=movie_update_fields, movie_id=movie_id, db=db)
    return result
