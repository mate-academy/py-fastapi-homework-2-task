from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, timedelta

from ..database import get_db
from ..models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from ..schemas.movies import (
    MovieListResponse,
    MovieCreateRequest,
    MovieDetailResponse,
    MovieUpdateRequest
)

router = APIRouter()


@router.get("/", response_model=MovieListResponse)
def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: Session = Depends(get_db)
):
    total_items = db.query(func.count(MovieModel.id)).scalar()
    total_pages = (total_items + per_page - 1) // per_page if total_items else 0

    if page > total_pages and total_pages > 0:
        raise HTTPException(status_code=404, detail="No movies found")

    offset = (page - 1) * per_page
    movies = db.query(MovieModel) \
        .order_by(desc(MovieModel.id)) \
        .offset(offset) \
        .limit(per_page) \
        .all()

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/", response_model=MovieDetailResponse, status_code=201)
def create_movie(data: MovieCreateRequest, db: Session = Depends(get_db)):
    # Date validation (fixed timedelta import)
    if data.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Date cannot be more than one year in the future")

    # Duplicate check
    if db.query(MovieModel).filter_by(name=data.name, date=data.date).first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists."
        )

    # Get or create country
    country = db.query(CountryModel).filter_by(code=data.country).first()
    if not country:
        country = CountryModel(code=data.country)
        db.add(country)
        db.flush()

    # Create movie
    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country_id=country.id
    )
    db.add(movie)
    db.flush()

    # Process associations
    for name, model in [
        (data.genres, GenreModel),
        (data.actors, ActorModel),
        (data.languages, LanguageModel)
    ]:
        for item in name:
            entity = db.query(model).filter_by(name=item).first()
            if not entity:
                entity = model(name=item)
                db.add(entity)
                db.flush()
            getattr(movie, model.__tablename__.rstrip('s')).append(entity)

    db.commit()
    return movie


@router.get("/{movie_id}/", response_model=MovieDetailResponse)
def get_movie(
        movie_id: int = Path(..., ge=1),
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).get(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/{movie_id}/", status_code=204)
def delete_movie(
        movie_id: int = Path(..., ge=1),
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).get(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()


# Fixed: removed default value for movie_data
@router.patch("/{movie_id}/", status_code=200)
def update_movie(
        movie_id: int = Path(..., ge=1),
        data: MovieUpdateRequest,  # Removed default value
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).get(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    # Check for duplicate
    if data.name or data.date:
        name = data.name or movie.name
        date = data.date or movie.date

        if db.query(MovieModel).filter(
                MovieModel.name == name,
                MovieModel.date == date,
                MovieModel.id != movie_id
        ).first():
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{name}' and release date '{date}' already exists."
            )

    # Update fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(movie, field, value)

    # Validate score
    if data.score is not None and (data.score < 0 or data.score > 100):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")

    db.commit()
    return {"detail": "Movie updated successfully."}
