from src.crud.movies import create_movie, get_movie, get_movies, update_movie, delete_movie
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.schemas.movies import MovieReadSchema, MovieCreateSchema, \
    MovieUpdateSchema

router = APIRouter()


@router.post("/movies/", response_model=MovieReadSchema)
def add_film(film: MovieCreateSchema, db: Session = Depends(get_db)):
    return create_movie(db, film)


@router.get("/movies/", response_model=list[MovieReadSchema])
def list_movies(db: Session = Depends(get_db)):
    db_movie = get_movies(db)
    if not db_movie:
        raise HTTPException(status_code=404, detail="No movies found for the specified page.")
    if db_movie:
        raise HTTPException(status_code=200)
    return db_movie


@router.get("/movies/{movie_id}", response_model=MovieReadSchema)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = get_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@router.put("/movies/{movie_id}", response_model=MovieReadSchema)
def edit_film(film_id: int, film: MovieUpdateSchema, db: Session = Depends(get_db)):
    db_movie = update_movie(db, film_id, film)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@router.delete("/movies/{movie_id}", response_model=MovieReadSchema)
def remove_film(movie_id: int, db: Session = Depends(get_db)):
    db_movie = delete_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Film not found")
    return db_movie
