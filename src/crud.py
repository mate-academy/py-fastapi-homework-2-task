from sqlalchemy import desc
from sqlalchemy.orm import Session
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieModel
)


def get_movies_on_page(page, per_page, db):
    return (
        db.query(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )


def get_movie_by_id(db, movie_id):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    return movie


def get_or_create_country(db: Session, country_name: str):
    country = (
        db.query(CountryModel)
        .filter(CountryModel.code == country_name)
        .first()
    )
    if not country:
        country = CountryModel(code=country_name)
        db.add(country)
        db.flush()
    return country


def get_or_create_genre(db: Session, genre_name: str):
    genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
    if not genre:
        genre = GenreModel(name=genre_name)
        db.add(genre)
        db.flush()
    return genre


def get_or_create_actor(db: Session, actor_name: str):
    actor = db.query(ActorModel).filter_by(name=actor_name).first()
    if not actor:
        actor = ActorModel(name=actor_name)
        db.add(actor)
        db.flush()
    return actor


def get_or_create_language(db: Session, language_name: str):
    language = db.query(LanguageModel).filter_by(name=language_name).first()
    if not language:
        language = LanguageModel(name=language_name)
        db.add(language)
        db.flush()
    return language


def create_new_movie(db_film, db):
    db.add(db_film)
    db.commit()
    db.refresh(db_film)
    return db_film
