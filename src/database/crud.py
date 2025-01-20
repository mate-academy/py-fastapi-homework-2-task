from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


def get_or_create(db, model, name_value):
    obj = db.query(model).filter(model.name == name_value).first()
    if not obj:
        obj = model(name=name_value)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def create_new_movie(db: Session, movie: MovieCreateSchema):
    existing_movie = (
        db.query(MovieModel)
        .filter(MovieModel.name == movie.name, MovieModel.date == movie.date)
        .first()
    )
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = [
        get_or_create(db, GenreModel, genre_name)
        for genre_name in movie.genres
    ]

    actors = [
        get_or_create(db, ActorModel, actor_name)
        for actor_name in movie.actors
    ]

    languages = [
        get_or_create(db, LanguageModel, lang_name)
        for lang_name in movie.languages
    ]

    new_movie = MovieModel(
        **movie.model_dump(exclude={"country", "genres", "actors", "languages"}),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie


def delete_movie_from_db(movie: MovieModel, db: Session) -> None:
    db.delete(movie)
    db.commit()


def update_movie_in_db(movie: MovieModel, movie_data: MovieUpdateSchema, db: Session) -> MovieModel:
    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    db.commit()
    db.refresh(movie)
    return movie
