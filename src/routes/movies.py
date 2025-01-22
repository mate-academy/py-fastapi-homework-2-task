from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from starlette.requests import Request

from crud.movies import (crud_create_movie, get_create, get_movie_by_id,
                         get_movies_pagination)
from database import get_db
from database.models import (ActorModel, CountryModel, GenreModel,
                             LanguageModel, MovieModel)
from schemas.movies import (ActorResponse, CountryResponse, GenreResponse,
                            LanguageResponse, MovieCreateRequest,
                            MovieCreateResponse, MovieDetailResponse,
                            MovieListResponse, MovieSchema, MovieUpdateRequest)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponse)
def get_movies(
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page"),
        db: Session = Depends(get_db),
):
    total_items = db.query(MovieModel).count()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page not found.")

    offset = (page - 1) * per_page
    movies, total_items = get_movies_pagination(offset, per_page, db)

    movies_list = [
        MovieSchema(
            id=movie.id,
            name=movie.name,
            date=str(movie.date),
            score=movie.score,
            overview=movie.overview
        )
        for movie in movies
    ]

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponse(
        movies=movies_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieCreateResponse, status_code=201)
def create_movie(movie: MovieCreateRequest, db: Session = Depends(get_db)):
    existing_movie = get_create(movie.name, movie.date, db)

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    try:
        new_movie = crud_create_movie(movie, db)
        return MovieCreateResponse.model_validate(new_movie)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponse)
def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    movie_details = get_movie_by_id(db, movie_id)
    if not movie_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return movie_details


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    db.delete(movie)
    db.commit()
    return None


@router.patch("/movies/{movie_id}/")
def update_movie(movie_id: int, movie_data: MovieUpdateRequest, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    if movie_data.name:
        movie.name = movie_data.name
    if movie_data.date:
        movie.date = movie_data.date
    if movie_data.score is not None:
        movie.score = movie_data.score
    if movie_data.overview:
        movie.overview = movie_data.overview
    if movie_data.status:
        movie.status = movie_data.status
    if movie_data.budget is not None:
        movie.budget = movie_data.budget
    if movie_data.revenue is not None:
        movie.revenue = movie_data.revenue

    db.commit()

    return {"detail": "Movie updated successfully."}
