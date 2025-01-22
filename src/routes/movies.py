from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import (MovieModel,
                             CountryModel,
                             GenreModel,
                             ActorModel,
                             LanguageModel)
from schemas.movies import (MoviesBase,
                            MovieBase,
                            MovieDetailSchema,
                            MovieCreateSchema,
                            CountryBase,
                            GenreBase,
                            ActorBase,
                            LanguageBase,
                            MovieUpdateSchema)

router = APIRouter()


# get all movies
@router.get("/movies/", response_model=MoviesBase)
def get_movies(db: Session = Depends(get_db),
               page: int = Query(1, ge=1),
               per_page: int = Query(10, ge=1)) -> MoviesBase:
    movies = db.query(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).order_by(desc(MovieModel.id)).limit(per_page).offset((page - 1) * per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if len(movies) == per_page else None
    total_pages = (db.query(MovieModel).count() + per_page - 1) // per_page
    total_items = db.query(MovieModel).count()

    return MoviesBase(
        movies=[
            MovieBase(
                id=movie.id,
                name=movie.name,
                date=movie.date,
                score=movie.score,
                overview=movie.overview
            ) for movie in movies
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_items=total_items,
        total_pages=total_pages
    )


# movie creation
@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)) -> MovieDetailSchema:
    movie_found = db.query(MovieModel).filter(MovieModel.name == movie.name, MovieModel.date == movie.date).first()

    if movie_found:
        raise HTTPException(status_code=409, detail=f"A movie with the name"
                                                    f" '{movie.name}' and"
                                                    f" release date '{movie.date}' already exists.")

    country = db.query(CountryModel).filter(CountryModel.name == movie.country).first()

    if not country:
        country = CountryModel(name=movie.country, code=f"{movie.country}")
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for genre in movie.genres:
        genre_found = db.query(GenreModel).filter(GenreModel.name == genre).first()
        if not genre_found:
            genre_found = GenreModel(name=genre)
            db.add(genre_found)
            db.commit()
            db.refresh(genre_found)
        genres.append(genre_found)

    actors = []
    for actor in movie.actors:
        actor_found = db.query(ActorModel).filter(ActorModel.name == actor).first()
        if not actor_found:
            actor_found = ActorModel(name=actor)
            db.add(actor_found)
            db.commit()
            db.refresh(actor_found)
        actors.append(actor_found)

    languages = []
    for language in movie.languages:
        language_found = db.query(LanguageModel).filter(LanguageModel.name == language).first()
        if not language_found:
            language_found = LanguageModel(name=language)
            db.add(language_found)
            db.commit()
            db.refresh(language_found)
        languages.append(language_found)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
        budget=movie.budget,
        revenue=movie.revenue
    )

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie


# get movie by id
@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailSchema:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


# delete movie
@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(movie)
    db.commit()


# update movie
@router.patch("/movies/{movie_id}/", status_code=200)
def update_movie(movie_id: int, movie: MovieUpdateSchema, db: Session = Depends(get_db)) -> dict[str, str]:
    existing_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for field, value in movie.model_dump(exclude_unset=True).items():
        if value:
            setattr(existing_movie, field, value)

    try:
        db.commit()
        db.refresh(existing_movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
