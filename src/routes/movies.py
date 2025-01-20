from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud as movies_crud
from database import get_db
from schemas.movies import (
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieDetailResponseSchema,

    MovieUpdateRequestSchema, MovieListSchema,
)


router = APIRouter()

@router.get("/movies/", response_model=MovieListSchema)
def get_movies_list(
    db: Session = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    return movies_crud.get_all_movies(db=db, page=page, per_page=per_page)


@router.get("/movies/{movie_id}", response_model=MovieDetailResponseSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailResponseSchema:
    movie = movies_crud.get_movie_by_id(movie_id, db)

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    return MovieDetailResponseSchema.model_validate(movie)


@router.post("/movies/", response_model=MovieCreateResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: Session = Depends(get_db),
) -> MovieCreateResponseSchema:
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


# @router.post("/movies/", response_model=MovieCreateResponseSchema,  status_code=status.HTTP_201_CREATED)
# def add_movie(film: MovieCreateRequestSchema, db: Session = Depends(get_db)):
#     return movies_crud.create_movie(db=db, film=film)


@router.patch("/movies/{movie_id}")
def update_movie(movie_id: int, movie_data: MovieUpdateRequestSchema, db: Session = Depends(get_db)) -> dict[str, str]:
    movie_to_update = movies_crud.get_movie_by_id(movie_id, db)

    if not movie_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    try:
        movies_crud.update_movie(movie_to_update, movie_data, db)
        return {"detail": "Movie updated successfully."}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data.")


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> None:
    movie_to_delete = movies_crud.get_movie_by_id(movie_id, db)

    if not movie_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    movies_crud.delete_movie(movie_to_delete, db)
