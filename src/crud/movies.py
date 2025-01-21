from datetime import datetime
from typing import Type

from sqlalchemy.orm import Session

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateResponseSchema, MovieUpdateRequestSchema


def get_movies_with_pagination(offset: int, per_page: int, db: Session) -> tuple[list[Type[MovieModel]], int]:
    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()
    movies_count = db.query(MovieModel).count()

    return movies, movies_count


def get_movie_by_name_and_date(name: str, date: datetime.date, db: Session) -> MovieModel | None:
    return db.query(MovieModel).filter(MovieModel.name == name, MovieModel.date == date).first()


def get_movie_by_id(id: int, db: Session) -> MovieModel | None:
    return db.query(MovieModel).filter(MovieModel.id == id).first()


def create_movie(movie_data: MovieCreateResponseSchema, db: Session) -> MovieModel:
    country = db.query(CountryModel).filter(CountryModel.code == movie_data.country).first()

    if not country:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        db.flush()

    genres = [
        db.query(GenreModel).filter(GenreModel.name == name).first() or GenreModel(name=name)

        for name in movie_data.genres
    ]

    actors = [
        db.query(ActorModel).filter(ActorModel.name == name).first() or ActorModel(name=name)

        for name in movie_data.actors
    ]

    languages = [
        db.query(LanguageModel).filter(LanguageModel.name == name).first() or LanguageModel(name=name)

        for name in movie_data.languages
    ]

    new_movie = MovieModel(
        **movie_data.model_dump(exclude={"country", "genres", "actors", "languages"}),
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie


def delete_movie(movie: MovieModel, db: Session):
    db.delete(movie)
    db.commit()


def update_movie(movie: MovieModel, movie_data: MovieUpdateRequestSchema, db: Session) -> MovieModel:
    movie_to_update = movie_data.model_dump(exclude_unset=True)

    for field, value in movie_to_update.items():
        setattr(movie, field, value)

    db.commit()
    db.flush(movie)

    return movie
