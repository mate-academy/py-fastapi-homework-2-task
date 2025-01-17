from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from crud import movies as movies_crud
from database import get_db
from schemas.movies import (
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieDetailResponseSchema,
    MovieListReadResponseSchema,
    MovieListResponseSchema,
    MovieUpdateRequestSchema,
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Number of movies per page"),
    db: Session = Depends(get_db),
) -> MovieListResponseSchema:
    """Get paginated list of movies."""
    offset = (page - 1) * per_page
    movies_query, total_movies = movies_crud.get_movies_with_pagination(offset, per_page, db)
    total_pages = (total_movies + per_page - 1) // per_page

    if page > total_pages or not total_movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieListReadResponseSchema.model_validate(movie) for movie in movies_query],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_movies,
    )


@router.post("/movies/", response_model=MovieCreateResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: Session = Depends(get_db),
) -> MovieCreateResponseSchema:
    """
    Creates a new movie with all relationships.
    If related entities don't exist, they will be created.
    """
    existing_movie = movies_crud.get_movie_by_name_and_date(movie_data.name, movie_data.date, db)

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    try:
        new_movie = movies_crud.create_movie(movie_data, db)
        return MovieCreateResponseSchema.model_validate(new_movie)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")


@router.get("/movies/{movie_id}", response_model=MovieDetailResponseSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailResponseSchema:
    """Get detailed movie information by ID."""
    movie = movies_crud.get_movie_by_id(movie_id, db)

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    return MovieDetailResponseSchema.model_validate(movie)


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> None:
    """Delete movie by ID."""
    movie_to_delete = movies_crud.get_movie_by_id(movie_id, db)

    if not movie_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    movies_crud.delete_movie(movie_to_delete, db)


@router.patch("/movies/{movie_id}")
def update_movie(movie_id: int, movie_data: MovieUpdateRequestSchema, db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Partially updates movie information. Only provided fields will be updated.
    Relationships cannot be updated.
    """
    movie_to_update = movies_crud.get_movie_by_id(movie_id, db)

    if not movie_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    try:
        movies_crud.update_movie(movie_to_update, movie_data, db)
        return {"detail": "Movie updated successfully."}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")
