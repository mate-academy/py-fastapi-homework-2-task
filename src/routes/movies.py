from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List

from src.schemas.movies import (
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieCreateSchema,
    MovieUpdateSchema
)
from src.database.models import MovieModel, GenreModel, ActorModel, LanguageModel

from src.database import get_db


router = APIRouter(prefix="/movies", tags=["Movies"])


# [1] Implement Movies List Endpoint
@router.get("/", response_model=MovieListResponseSchema)
def get_movies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    query = select(MovieModel).offset(skip).limit(limit)
    movies = db.execute(query).scalars().all()

    total_count = db.execute(select(func.count(MovieModel.id))).scalar()

    return {"items": movies, "total": total_count}


# [2] Implement Movie Creation Endpoint
@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie_data: MovieCreateSchema, db: Session = Depends(get_db)):
    new_movie = MovieModel(
        **movie_data.model_dump(exclude={"genre_ids", "actor_ids", "language_ids"})
    )

    if movie_data.genre_ids:
        genres = db.execute(select(GenreModel).where(GenreModel.id.in_(movie_data.genre_ids))).scalars().all()
        new_movie.genres = list(genres)

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


# [3] Implement Movie Details Endpoint
@router.get("/{movie_id}", response_model=MovieDetailSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# [4] Implement Movie Deletion Endpoint
@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(movie)
    db.commit()
    return None


# [5] Implement Movie Update Endpoint
@router.patch("/{movie_id}", response_model=MovieDetailSchema)
def update_movie(movie_id: int, movie_update: MovieUpdateSchema, db: Session = Depends(get_db)):
    movie_db = db.get(MovieModel, movie_id)
    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie not found")

    update_data = movie_update.model_dump(exclude_unset=True)

    if "genre_ids" in update_data:
        ids = update_data.pop("genre_ids")
        genres = db.execute(select(GenreModel).where(GenreModel.id.in_(ids))).scalars().all()
        movie_db.genres = list(genres)

    for key, value in update_data.items():
        setattr(movie_db, key, value)

    db.commit()
    db.refresh(movie_db)
    return movie_db
