from datetime import datetime

from sqlalchemy.orm import Session

from database.models import (ActorModel, CountryModel, GenreModel,
                             LanguageModel, MovieModel)
from schemas.movies import MovieCreateRequest


def get_movies_pagination(offset: int, per_page: int, db: Session) -> tuple[list[type[MovieModel]], int]:
    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()
    movies_count = db.query(MovieModel).count()
    return movies, movies_count


def get_movie_by_id(db: Session, movie_id: int) -> MovieModel | None:
    return db.query(MovieModel).filter(MovieModel.id == movie_id).first()


def get_create(name: str, date: datetime.date, db: Session) -> MovieModel | None:
    return db.query(MovieModel).filter(MovieModel.name == name, MovieModel.date == date).first()


def crud_create_movie(movie: MovieCreateRequest, db: Session) -> MovieModel:
    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for genre_name in movie.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.commit()
            db.refresh(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.commit()
            db.refresh(actor)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.commit()
            db.refresh(language)
        languages.append(language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages
    db.commit()

    return new_movie
