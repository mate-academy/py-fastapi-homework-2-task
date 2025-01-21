from datetime import date

from sqlalchemy.orm import Session

from database import MovieModel
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import MovieCreateRequestSchema, MovieUpdateRequestSchema


def create_movie_in_db(movie_data: MovieCreateRequestSchema, db: Session):
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
        languages=languages,
    )

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie


def update_movie_in_db(movie: MovieModel, movie_data: MovieUpdateRequestSchema, db: Session):
    update_data = movie_data.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        setattr(movie, field_name, value)

    db.commit()
