from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from database.crud import create_new_movie, delete_movie_from_db, update_movie_in_db
from database.models import MovieModel

from schemas.movies import (
    MovieCreateSchema,
    MovieReadResponseSchema,
    MovieResponseSchema,
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieUpdateSchema
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
def get_movies(
        db: Session = Depends(get_db),
        page: int = Query(
            default=1,
            ge=1,
            description="Page number, starting from 1"
        ),
        per_page: int = Query(
            default=10,
            ge=1,
            le=20,
            description="Number of movies per page"
        )
):
    offset = (page - 1) * per_page

    total_items = db.query(MovieModel).count()
    movies = db.query(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    prev_page = (f"/theater/movies/?page={page - 1}"
                 f"&per_page={per_page}") if page > 1 else None
    next_page = (f"/theater/movies/?page={page + 1}"
                 f"&per_page={per_page}") if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieReadResponseSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):
    try:
        new_movie = create_new_movie(db, movie)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error occurred: " + str(exc),
        )
    return new_movie


@router.get(
    "/movies/{movie_id}",
    response_model=MovieDetailResponseSchema
)
def get_film(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> None:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    delete_movie_from_db(movie, db)

@router.patch("/movies/{movie_id}")
def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: Session = Depends(get_db)) -> dict[str, str]:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    try:
        update_movie_in_db(movie, movie_data, db)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
