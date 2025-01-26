from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from database.models import MovieModel
from routes.crud import create_movie, delete_movie, update_movie
from schemas.movies import MovieList, MovieBase, MovieDetail, MovieCreate, MovieUpdate

router = APIRouter()


@router.get("/movies/", response_model=MovieList)
def list_movies(
        page: int = Query(1, ge=1, description="The page number to fetch"),
        per_page: int = Query(10, ge=1, le=20, description="Number of movies per page"),
        db: Session = Depends(get_db)
):
    if page < 1:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "page"],
                    "msg": "ensure this value is greater than or equal to 1",
                    "type": "value_error.number.not_ge"
                }
            ]
        )

    if per_page < 1 or per_page > 20:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "per_page"],
                    "msg": "ensure this value is between 1 and 20",
                    "type": "value_error.number.not_in_range"
                }
            ]
        )
    movies = db.query(MovieModel)
    total_items = movies.count()
    total_pages = ceil(total_items / per_page)

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    offset = (page - 1) * per_page
    movies_query = movies.order_by(-MovieModel.id).offset(offset).limit(per_page).all()

    if not movies_query:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies_data = [MovieBase.model_validate(movie) for movie in movies_query]

    return MovieList(
        movies=movies_data,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetail, status_code=201)
def add_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    return create_movie(db, movie)


@router.get("/movies/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return db_movie


@router.delete("/movies/{movie_id}", status_code=204)
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    delete_movie(db, movie_id)
    return


@router.patch("/movies/{movie_id}", status_code=200)
def edit_movie(movie_id: int, movie: MovieUpdate, db: Session = Depends(get_db)):
    return update_movie(db, movie_id, movie)
