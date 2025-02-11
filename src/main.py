import math


from fastapi import APIRouter, Depends, HTTPException, Query, Path

from sqlalchemy.orm import Session

from crud.movies import get_movies, create_movie, get_movie, delete_movie, update_movie
from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)

from schemas.movies import (
    MovieListSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    MoviePageSchema
)


router = APIRouter()


@router.get("/movies/", response_model=MoviePageSchema)
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    movies_data = get_movies(db, offset, per_page)

    if movies_data:

        total_items = db.query(MovieModel).count()
        total_pages = math.ceil(total_items / per_page)

        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

        return {
            "movies": movies_data,
            "prev_page": prev_page,
            "next_page": next_page,
            "total_pages": total_pages,
            "total_items": total_items
        }
    raise HTTPException(status_code=404, detail="No movies found.")


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(
        movie_id: int = Path(..., gt=0),
        db: Session = Depends(get_db)
):
    movie = get_movie(db, movie_id)
    if movie:
        return movie
    raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
def add_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):
    movies = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).all()
    if not movies:
        return create_movie(db, movie)
    raise HTTPException(
        status_code=409,
        detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
    )


@router.delete("/movies/{movie_id}/", status_code=204)
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    delete_movie(db, movie_id)


@router.patch("/movies/{movie_id}/")
def patch_movie(movie_id: int, movie: MovieUpdateSchema, db: Session = Depends(get_db)):
    update_movie(db, movie_id, movie)
    return HTTPException(status_code=200, detail="Movie updated successfully.")