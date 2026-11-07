from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError
from starlette.responses import JSONResponse

from crud import get_movies, create_movie, get_movie_by_id, remove_movie, edit_movie
from routes.dependencies import PaginationDep, SessionDep
from schemas.movies import MovieListResponseSchema, MovieCreateSchema, MovieDetailSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
        request: Request,
        params: PaginationDep,
        db: SessionDep
):
    movies = await get_movies(
        request=request,
        page=params["page"],
        per_page=params["per_page"],
        db=db
    )
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return movies


@router.post("/movies/", status_code=201, response_model=MovieDetailSchema)
async def add_movie(movie_data: dict, db: SessionDep):
    try:
        movie = MovieCreateSchema(**movie_data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid movie data")

    db_movie = await create_movie(movie=movie, db=db)
    return db_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def retrieve_movie(movie_id: int, db: SessionDep):
    db_movie = await get_movie_by_id(movie_id=movie_id, db=db)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return db_movie


@router.delete("/movies/{movie_id}/")
async def delete_movie(movie_id: int, db: SessionDep):
    db_movie = await get_movie_by_id(movie_id=movie_id, db=db)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await remove_movie(db_movie=db_movie, db=db)
    return JSONResponse(status_code=204, content=None)


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(movie_id: int, movie_data: dict, db: SessionDep):
    try:
        movie_update = MovieUpdateSchema(**movie_data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    db_movie = await get_movie_by_id(movie_id=movie_id, db=db)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await edit_movie(db_movie=db_movie, movie_update=movie_update, db=db)

    return {"detail": "Movie updated successfully."}
