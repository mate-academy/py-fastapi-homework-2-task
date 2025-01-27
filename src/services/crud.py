from typing import Annotated, Optional

from fastapi import Depends, Query, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieSchema,
    CreateMovieSchema,
    MovieDetailSchema,
)


def get_movies(
        db: Session = Depends(get_db),
        offset: Optional[int] = None,
        limit: Optional[int] = None
):
    query = db.query(MovieModel).order_by(MovieModel.id.desc())

    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    return query.all()


def create_movie(
        movie: CreateMovieSchema,
        db: Session = Depends(get_db)
):
    try:
        country = get_or_create_country(movie.country, db)

        genres = [get_or_create_genre(genre, db) for genre in movie.genres]
        actors = [get_or_create_actor(actor, db) for actor in movie.actors]
        languages = [get_or_create_language(language, db) for language in movie.languages]

        new_movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages
        )

        db.add(new_movie)
        db.commit()
        db.refresh(new_movie)

        return new_movie
    except Exception as e:
        db.rollback()
        raise e


def get_or_create_country(country_code: str, db: Session):
    country = db.query(CountryModel).filter_by(code=country_code).first()
    if not country:
        country = CountryModel(code=country_code)
        db.add(country)
        db.flush()
    return country


def get_or_create_genre(genre_name: str, db: Session):
    genre = db.query(GenreModel).filter_by(name=genre_name).first()
    if not genre:
        genre = GenreModel(name=genre_name)
        db.add(genre)
        db.flush()
    return genre


def get_or_create_actor(actor_name: str, db: Session):
    actor = db.query(ActorModel).filter_by(name=actor_name).first()
    if not actor:
        actor = ActorModel(name=actor_name)
        db.add(actor)
        db.flush()
    return actor


def get_or_create_language(language_name: str, db: Session):
    language = db.query(LanguageModel).filter_by(name=language_name).first()
    if not language:
        language = LanguageModel(name=language_name)
        db.add(language)
        db.flush()
    return language


def get_movie_by_id(db: Session, movie_id: int) -> MovieModel | None:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


def delete_movie(db: Session, movie_id: int) -> None:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    db.delete(movie)
    db.commit()


def update_movie(db: Session, movie_id: int, updated_data: dict) -> None:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    for key, value in updated_data.items():
        if hasattr(movie, key):
            setattr(movie, key, value)

    db.commit()
