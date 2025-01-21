import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, exists

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieBaseResponseSchema,
    MovieCreateRequestSchema,
    MovieReadResponseSchema,
    MovieUpdateRequestSchema,
)
from crud.movies import create_movie_in_db, update_movie_in_db


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
def get_movies(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
    db: Session = Depends(get_db),
):
    start = (page - 1) * per_page
    movies = db.query(MovieModel).order_by(desc(MovieModel.id)).offset(start).limit(per_page).all()

    total_items = db.query(MovieModel).count()
    total_pages = math.ceil(total_items / per_page)

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    if not movies or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieReadResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie_data: MovieCreateRequestSchema, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date).first()
    if movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )
    try:
        new_movie = create_movie_in_db(movie_data, db)
        return MovieReadResponseSchema.model_validate(new_movie)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=MovieReadResponseSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    moive = db.get(MovieModel, movie_id)
    if not moive:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return moive


@router.patch("/movies/{movie_id}/")
def update_movie(movie_id: int, movie_data: MovieUpdateRequestSchema, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    update_movie_in_db(movie, movie_data, db)
    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()
