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
def list_films(db: Session = Depends(get_db)):
    return get_movies(db)


@router.get("/movies/{film_id}", response_model=MovieReadSchema)
def read_film(film_id: int, db: Session = Depends(get_db)):
    db_film = get_movie(db, film_id)
    if not db_film:
        raise HTTPException(status_code=404, detail="Film not found")
    return db_film


@router.put("/movies/{film_id}", response_model=MovieReadSchema)
def edit_film(film_id: int, film: MovieUpdateSchema, db: Session = Depends(get_db)):
    db_film = update_movie(db, film_id, film)
    if not db_film:
        raise HTTPException(status_code=404, detail="Film not found")
    return db_film


@router.delete("/movies/{film_id}", response_model=MovieReadSchema)
def remove_film(film_id: int, db: Session = Depends(get_db)):
    db_film = delete_movie(db, film_id)
    if not db_film:
        raise HTTPException(status_code=404, detail="Film not found")
    return db_film
