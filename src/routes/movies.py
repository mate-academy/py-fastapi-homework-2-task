import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from ..database import get_db
from ..models import (
    MovieModel, CountryModel, GenreModel,
    ActorModel, LanguageModel, MovieStatusEnum
)
from ..schemas.movies import (
    MovieListResponseSchema,
    MovieCreateRequestSchema,
    MovieDetailResponseSchema,
    MovieUpdateRequestSchema
)

router = APIRouter()


# Helper function to create/get associated entities
def get_or_create_entities(db: Session, names: list[str], model):
    entities = []
    for name in names:
        entity = db.query(model).filter(model.name == name).first()
        if not entity:
            entity = model(name=name)
            db.add(entity)
            db.flush()
        entities.append(entity)
    return entities


# 1. Movie List Endpoint
@router.get("/", response_model=MovieListResponseSchema)
def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: Session = Depends(get_db)
):
    # Calculate offset and fetch data
    offset = (page - 1) * per_page
    total_items = db.query(func.count(MovieModel.id)).scalar()
    total_pages = (total_items + per_page - 1) // per_page if total_items else 0

    # Validate page
    if total_pages > 0 and page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found"
        )

    # Fetch paginated movies
    movies = db.query(MovieModel) \
        .order_by(desc(MovieModel.id)) \
        .offset(offset) \
        .limit(per_page) \
        .all()

    # Build pagination URLs
    base_url = "/theater/movies/"
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


# 2. Movie Creation Endpoint
@router.post("/", response_model=MovieDetailResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie_data: MovieCreateRequestSchema, db: Session = Depends(get_db)):
    # Duplicate check
    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    ).first()
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # Handle country
    country = db.query(CountryModel).filter(CountryModel.code == movie_data.country).first()
    if not country:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        db.flush()

    # Create movie
    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id
    )
    db.add(movie)
    db.flush()

    # Handle associations
    movie.genres = get_or_create_entities(db, movie_data.genres, GenreModel)
    movie.actors = get_or_create_entities(db, movie_data.actors, ActorModel)
    movie.languages = get_or_create_entities(db, movie_data.languages, LanguageModel)

    db.commit()
    db.refresh(movie)
    return movie


# 3. Movie Details Endpoint
@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
def get_movie_details(
        movie_id: int = Path(..., title="The ID of the movie to retrieve", ge=1),
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return movie


# 4. Movie Deletion Endpoint
@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
        movie_id: int = Path(..., title="The ID of the movie to delete", ge=1),
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    db.delete(movie)
    db.commit()


# 5. Movie Update Endpoint
@router.patch("/{movie_id}/", status_code=status.HTTP_200_OK)
def update_movie(
        movie_id: int = Path(..., title="The ID of the movie to update", ge=1),
        movie_data: MovieUpdateRequestSchema = None,
        db: Session = Depends(get_db)
):
    # Get movie
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    # Check for duplicate if name or date is being updated
    if movie_data.name or movie_data.date:
        new_name = movie_data.name if movie_data.name else movie.name
        new_date = movie_data.date if movie_data.date else movie.date

        existing_movie = db.query(MovieModel).filter(
            MovieModel.name == new_name,
            MovieModel.date == new_date,
            MovieModel.id != movie_id
        ).first()

        if existing_movie:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A movie with the name '{new_name}' and release date '{new_date}' already exists."
            )

    # Update fields
    update_data = movie_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    # Validate score if provided
    if movie_data.score is not None and not (0 <= movie_data.score <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score must be between 0 and 100"
        )

    db.commit()
    db.refresh(movie)
    return {"detail": "Movie updated successfully."}
