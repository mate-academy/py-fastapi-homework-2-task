from src.crud.movies import create_movie, get_movie, get_movies, update_movie, delete_movie
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.models import MovieModel
from src.schemas.movies import MovieReadSchema, MovieCreateSchema, \
    MovieUpdateSchema

router = APIRouter()


@router.post("/movies/", response_model=MovieReadSchema)
def add_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):
    return create_movie(db, movie)


@router.get("/movies/", response_model=list[MovieReadSchema], status_code=200)
def list_movies(db: Session = Depends(get_db)):
    db_movie = get_movies(db)
    return db_movie


@router.get("/movies/{movie_id}", response_model=MovieReadSchema)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = get_movie(db, movie_id)
    return db_movie


@router.patch("/movies/{movie_id}", response_model=MovieReadSchema, status_code=200)
def edit_movie(movie_id: int, movie: MovieUpdateSchema, db: Session = Depends(get_db)):
    db_movie = update_movie(db, movie_id, movie)
    return db_movie


@router.delete("/movies/{movie_id}", response_model=MovieReadSchema, status_code=204)
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = delete_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return db_movie
