from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Path
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload, Session

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from src.schemas.movies import MovieCreate, MovieUpdate, MovieDetailSchema, MovieListResponseSchema
import math


router = APIRouter()


movie_router = APIRouter(prefix="/movies")

# Utility
def get_or_create(db: Session, model, field: str, value: str):
    instance = db.query(model).filter(getattr(model, field) == value).first()
    if not instance:
        instance = model(**{field: value})
        db.add(instance)
        db.flush()
    return instance

# 1. GET /movies/ list
@movie_router.get("/", response_model=MovieListResponseSchema)
def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    total_items = db.query(func.count(MovieModel.id)).scalar()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    movies = (
        db.query(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    base_url = str(request.url).split("?")[0]
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page+1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )

# 2. POST /movies/
@movie_router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
def create_movie(payload: MovieCreate, db: Session = Depends(get_db)):
    exists = db.query(MovieModel).filter_by(name=payload.name, date=payload.date).first()
    if exists:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists."
        )

    country = get_or_create(db, CountryModel, "code", payload.country)

    genres = [get_or_create(db, GenreModel, "name", g.strip()) for g in payload.genres]
    actors = [get_or_create(db, ActorModel, "name", a.strip()) for a in payload.actors]
    languages = [get_or_create(db, LanguageModel, "name", l.strip()) for l in payload.languages]

    movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie

# 3. GET /movies/{movie_id}/
@movie_router.get("/{movie_id}/", response_model=MovieDetailSchema)
def get_movie(movie_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie

# 4. DELETE /movies/{movie_id}/
@movie_router.delete("/{movie_id}/", status_code=204)
def delete_movie(movie_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()
    return

# 5. PATCH /movies/{movie_id}/
@movie_router.patch("/{movie_id}/")
def update_movie(
    movie_id: int = Path(..., ge=1),
    payload: MovieUpdate = ...,
    db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(movie, key, value)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}