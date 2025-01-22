from database import get_db
from fastapi import Depends, Query, HTTPException
from models import MovieModel
from schemas import MovieCreateSchema, MovieUpdateSchema
from sqlalchemy.orm import Session


def create_movie(db: Session, movie: MovieCreateSchema):
    db_movie = MovieModel(**movie.dict())
    db_movie = (
        db.query(MovieModel)
        .filter(MovieModel.name == movie.name, MovieModel.date == movie.date)
        .first()
    )
    if db_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )
    if db_movie is None:
        raise HTTPException(status_code=400)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


def get_movies(
        page: int = Query(default=1, ge=1, description="The page number(>= 1)"),
        per_page: int = Query(default=10, ge=1, le=20, description="Film quantity at the page (>= 1 и <= 20)"),
        db: Session = Depends(get_db)
):
    total_items = db.query(MovieModel).count()
    offset = (page - 1) * per_page
    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()
    base_url = "/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if offset + per_page < total_items else None
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found for the specified page.")
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": (total_items + per_page - 1) // per_page,
        "total_items": total_items,
    }


def update_movie(db: Session, movie_id: int, movie: MovieUpdateSchema):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    if db_movie is None:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    db_movie.title = movie.title
    db_movie.genre = movie.genre
    db_movie.price = movie.price
    db.commit()
    db.refresh(db_movie)
    return db_movie


def delete_movie(db: Session, movie_id: int):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        return None
    db.delete(db_movie)
    db.commit()
    return db_movie
