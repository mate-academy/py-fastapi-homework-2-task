import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse, Response

from database import get_db

from crud.crud import get_movies, get_movie, create_movie, delete_movie, update_movie
from src.schemas.movies import PaginatedMovies, DetailedMovies, MovieUpdate, MovieCreate

router = APIRouter()


@router.get("/movies/{movie_id}", response_model=DetailedMovies)
def movie(movie_id: int, db: Session = Depends(get_db)):
    movie = get_movie(movie_id, db)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}")
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    delete_movie(movie_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}")
def patch_movie(movie_id: int, movie_data: MovieUpdate, db: Session = Depends(get_db)):
    return update_movie(movie_id, movie_data, db)


@router.get("/movies/", response_model=PaginatedMovies)
def movies_list(
        page: int = 1,
        per_page: int = 10,
        db: Session = Depends(get_db)
):
    return get_movies(page, per_page, db)


@router.post("/movies/", response_model=MovieCreate)
def add_movie(movie_data: MovieCreate, db: Session = Depends(get_db)):
    movie = create_movie(movie_data, db)
    movie_dict = movie.model_dump()

    if isinstance(movie_dict.get("date"), datetime.date):
        movie_dict["date"] = movie_dict["date"].isoformat()

    return JSONResponse(
        content=movie_dict,
        status_code=status.HTTP_201_CREATED
    )
