from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieListResponseSchema, MovieCreateResponseSchema, MovieDetailResponseSchema, \
    MovieUpdateResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
def get_films(
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
        db: Session = Depends(get_db)
):
    movies = db.query(MovieModel).order_by(desc(MovieModel.id)).offset((page - 1) * per_page).limit(per_page)
    if movies.count() == 0:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_items = db.query(MovieModel).count()
    total_pages = -int(-(total_items / per_page) // 1)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance
    else:
        kwargs |= defaults or {}
        instance = model(**kwargs)
        try:
            session.add(instance)
            session.commit()
        except Exception:
            session.rollback()
            instance = session.query(model).filter_by(**kwargs).one()
            return instance
        else:
            return instance


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
def add_film(movie: MovieCreateResponseSchema, db: Session = Depends(get_db)):
    movie_dict = movie.dict()
    movie_dict["country"] = get_or_create(db, CountryModel, code=movie_dict["country"])
    movie_dict["genres"] = [get_or_create(db, GenreModel, name=genre_kwargs) for genre_kwargs in movie_dict["genres"]]
    movie_dict["actors"] = [get_or_create(db, ActorModel, name=actor_kwargs) for actor_kwargs in movie_dict["actors"]]
    movie_dict["languages"] = [
        get_or_create(db, LanguageModel, name=lang_kwargs) for lang_kwargs in movie_dict["languages"]
    ]
    db_movie = MovieModel(**movie_dict)
    try:
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{db_movie.name}' and release date '{db_movie.date}' already exists."
        )
    return db_movie


@router.get("/movies/{movie_id}", response_model=MovieDetailResponseSchema, status_code=200)
def read_film(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return db_movie


@router.delete("/movies/{movie_id}", status_code=204)
def remove_film(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(db_movie)
    db.commit()


@router.patch("/movies/{movie_id}", status_code=200,)
def edit_film(
        movie_id: int,
        movie: MovieUpdateResponseSchema,
        db: Session = Depends(get_db)
):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    if movie.name:
        db_movie.name = movie.name
    if movie.date:
        db_movie.date = movie.date
    if movie.score:
        db_movie.score = movie.score
    if movie.overview:
        db_movie.overview = movie.overview
    if movie.status:
        db_movie.status = movie.status
    if movie.budget:
        db_movie.budget = movie.budget
    if movie.revenue:
        db_movie.revenue = movie.revenue
    try:
        db.commit()
        db.refresh(db_movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    return {"detail": "Movie updated successfully."}
