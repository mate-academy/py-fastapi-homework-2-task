from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status
from crud import movies as crud_movies

from database import get_db, MovieModel
from schemas.movies import (
    MovieListReadResponseSchema,
    MovieCreateResponseSchema,
    MovieCreateRequestSchema,
    MovieDetailResponseSchema,
    MovieUpdateRequestSchema,
    MovieListResponseSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
def read_movies(
        page: int = Query(ge=1, default=1),
        per_page: int = Query(ge=1, default=10),
        db: Session = Depends(get_db)
) -> MovieListResponseSchema:

    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    offset = (page - 1) * per_page
    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieCreateResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(
        movie_data: MovieCreateRequestSchema,
        db: Session = Depends(get_db)
) -> MovieCreateResponseSchema:
    existing_movie = crud_movies.get_movie_by_name_and_date(movie_data.name, movie_data.date, db)

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    try:
        new_movie = crud_movies.create_movie(movie_data, db)
        return MovieCreateResponseSchema.model_validate(new_movie)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailResponseSchema:
    movie = crud_movies.get_movie_by_id(movie_id, db)

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    return MovieDetailResponseSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> None:
    movie = crud_movies.get_movie_by_id(movie_id, db)

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    crud_movies.delete_movie(movie, db)


@router.patch("/movies/{movie_id}/")
def update_movie(movie_id: int, movie_data: MovieUpdateRequestSchema, db: Session = Depends(get_db)) -> dict[str, str]:
    movie_to_update = crud_movies.get_movie_by_id(movie_id, db)

    if not movie_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    try:
        crud_movies.update_movie(movie_to_update, movie_data, db)
        return {"detail": "Movie updated successfully."}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
