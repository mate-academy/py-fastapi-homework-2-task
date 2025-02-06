from typing import List

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieCreateSchema, MovieUpdateSchema


def get_movies(db: Session, offset, per_page):
    return db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()


def get_movie(db: Session, movie_id):
    return db.query(MovieModel).filter(MovieModel.id == movie_id).first()


def create_objects(data: List[str], model, db: Session):

    objects = [model(name=element) for element in data]
    db.add_all(objects)
    db.commit()

    for obj in objects:
        db.refresh(obj)

    return objects


def create_movie(db: Session, movie: MovieCreateSchema):

    try:

        country_data = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
        if not country_data:
            country_data = CountryModel(code=movie.country)
            db.add(country_data)
            db.commit()
            db.refresh(country_data)

        genres_data = db.query(GenreModel).filter(GenreModel.name.in_(movie.genres)).all()
        if not genres_data:
            genres_data = create_objects(movie.genres, GenreModel, db)

        actors_data = db.query(ActorModel).filter(ActorModel.name.in_(movie.actors)).all()
        if not actors_data:
            actors_data = create_objects(movie.actors, ActorModel, db)

        languages_data = db.query(LanguageModel).filter(LanguageModel.name.in_(movie.languages)).all()
        if not languages_data:
            languages_data = create_objects(movie.languages, LanguageModel, db)

        db_movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=country_data,
            genres=genres_data,
            actors=actors_data,
            languages=languages_data
        )

        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
        return db_movie

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


def delete_movie(db: Session, movie_id: int):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(db_movie)
    db.commit()


def update_movie(db: Session, movie_id: int, movie: MovieUpdateSchema):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for key, value in movie.dict(exclude_unset=True).items():
        setattr(db_movie, key, value)

    db.commit()
    db.refresh(db_movie)
