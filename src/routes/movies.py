from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from typing import List
import math

from database import get_db
from src.database.models import (
    MovieModel, CountryModel, GenreModel,
    ActorModel, LanguageModel, MovieStatusEnum
)
from schemas.movies import (
    MovieListResponseSchema, MovieCreateSchema,
    MovieDetailSchema, MovieUpdateSchema
)

router = APIRouter(prefix="/movies", tags=["Movies"])


# [1] Implement Movies List Endpoint
@router.get("/", response_model=MovieListResponseSchema)
def list_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: Session = Depends(get_db)
):
    total_items = db.execute(select(func.count(MovieModel.id))).scalar()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page

    if page > total_pages and total_items > 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = db.execute(
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    ).scalars().all()

    base_url = str(request.url).split('?')[0]

    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


# [2] Implement Movie Creation Endpoint
@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie_in: MovieCreateSchema, db: Session = Depends(get_db)):
    # Перевірка на дублікат
    existing = db.execute(
        select(MovieModel).where(MovieModel.name == movie_in.name, MovieModel.date == movie_in.date)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    country = db.execute(select(CountryModel).where(CountryModel.code == movie_in.country)).scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie_in.country)
        db.add(country)
        db.flush()

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country_id=country.id
    )

    def link_entities(model, names):
        entities = []
        for name in names:
            ent = db.execute(select(model).where(model.name == name)).scalar_one_or_none()
            if not ent:
                ent = model(name=name)
                db.add(ent)
                db.flush()
            entities.append(ent)
        return entities

    new_movie.genres = link_entities(GenreModel, movie_in.genres)
    new_movie.actors = link_entities(ActorModel, movie_in.actors)
    new_movie.languages = link_entities(LanguageModel, movie_in.languages)

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


# [3] Implement Movie Details Endpoint
@router.get("/{movie_id}/", response_model=MovieDetailSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


# [4] Implement Movie Deletion Endpoint
@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()
    return None


# [5] Implement Movie Update Endpoint
@router.patch("/{movie_id}/")
def update_movie(movie_id: int, movie_in: MovieUpdateSchema, db: Session = Depends(get_db)):
    movie_db = db.get(MovieModel, movie_id)
    if not movie_db:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_in.model_dump(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(movie_db, field, value)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
