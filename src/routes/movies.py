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
    existing_movie = (
        db.query(MovieModel)
        .filter(MovieModel.name == movie.name, MovieModel.date == movie.date)
        .first()
    )
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )
    if existing_movie is None:
        raise HTTPException(status_code=400)
    return create_movie(db, movie)

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
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return db_movie


@router.put("/movies/{movie_id}", response_model=MovieReadSchema)
def edit_movie(movie_id: int, movie: MovieUpdateSchema, db: Session = Depends(get_db)):
    db_movie = update_movie(db, movie_id, movie)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@router.delete("/movies/{movie_id}", response_model=MovieReadSchema)
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = delete_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie
