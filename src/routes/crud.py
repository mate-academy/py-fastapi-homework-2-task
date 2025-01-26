from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import MovieModel
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import MovieCreate, MovieUpdate


def get_movies(db: Session):
    return db.query(MovieModel).all()


def create_movie(db: Session, movie: MovieCreate):
    already_exist = db.query(MovieModel).filter(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    ).first()
    if already_exist:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        db.flush()

    genres = []
    for genre_name in movie.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
        languages.append(language)

    created_movie = MovieModel(
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
        languages=languages,
    )
    db.add(created_movie)
    db.commit()
    db.refresh(created_movie)
    return created_movie


def update_movie(db: Session, movie_id: int, movie: MovieUpdate):
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
    db.commit()
    db.refresh(db_movie)
    return {
        "detail": "Movie updated successfully."
    }


def delete_movie(db: Session, movie_id: int):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(db_movie)
    db.commit()
