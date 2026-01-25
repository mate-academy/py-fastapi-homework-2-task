from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from database import MovieModel
from database.models import GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieRead, MovieCreate, MovieUpdate

router = APIRouter(prefix="/movies", tags=["Movies"])


# [1] Implement Movies List Endpoint
@router.get("/", response_model=List[MovieRead])
def get_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    movies = db.execute(select(MovieModel).offset(skip).limit(limit)).scalars().all()
    return movies


# [2] Implement Movie Creation Endpoint
@router.post("/", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
def create_movie(movie_data: MovieCreate, db: Session = Depends(get_db)):
    # Створюємо об'єкт фільму без M2M зв'язків спочатку
    new_movie = MovieModel(
        **movie_data.model_dump(exclude={"genre_ids", "actor_ids", "language_ids"})
    )

    # Додаємо зв'язки (завантажуємо об'єкти з БД по ID)
    if movie_data.genre_ids:
        genres = db.execute(select(GenreModel).where(GenreModel.id.in_(movie_data.genre_ids))).scalars().all()
        new_movie.genres = list(genres)

    if movie_data.actor_ids:
        actors = db.execute(select(ActorModel).where(ActorModel.id.in_(movie_data.actor_ids))).scalars().all()
        new_movie.actors = list(actors)

    if movie_data.language_ids:
        langs = db.execute(select(LanguageModel).where(LanguageModel.id.in_(movie_data.language_ids))).scalars().all()
        new_movie.languages = list(langs)

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


# [3] Implement Movie Details Endpoint
@router.get("/{movie_id}", response_model=MovieRead)
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
@router.patch("/{movie_id}", response_model=MovieRead)
def update_movie(movie_id: int, movie_update: MovieUpdate, db: Session = Depends(get_db)):
    movie_db = db.get(MovieModel, movie_id)
    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie not found")

    update_dict = movie_update.model_dump(exclude_unset=True)

    # Окремо обробляємо M2M поля
    m2m_fields = {
        "genre_ids": (GenreModel, "genres"),
        "actor_ids": (ActorModel, "actors"),
        "language_ids": (LanguageModel, "languages"),
    }

    for field_name, (model, attr) in m2m_fields.items():
        if field_name in update_dict:
            ids = update_dict.pop(field_name)
            related_items = db.execute(select(model).where(model.id.in_(ids))).scalars().all()
            setattr(movie_db, attr, list(related_items))

    # Оновлюємо звичайні поля
    for key, value in update_dict.items():
        setattr(movie_db, key, value)

    db.commit()
    db.refresh(movie_db)
    return movie_db
