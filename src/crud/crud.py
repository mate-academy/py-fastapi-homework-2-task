import datetime
from math import ceil

from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from database.models import MovieModel, GenreModel, ActorModel, LanguageModel, CountryModel

from src.schemas.movies import MovieSchema, DetailedMovies, MovieUpdate


def get_movie(
        movie_id: int,
        db: Session
):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if movie:
        return DetailedMovies.model_validate(movie)
    raise HTTPException(
        status_code=404,
        detail="Movie with the given ID was not found."
    )


def get_movies(
        page: int,
        per_page: int,
        db: Session,
):

    if page < 1 or (per_page < 1 or per_page > 20):
        raise HTTPException(
            status_code=422,
            detail=[{"msg": "Input should be greater than or equal to 1"}]
        )

    total_items = db.query(func.count(MovieModel.id)).scalar()
    total_pages = ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    movie_list = (
        db
        .query(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    movies = [MovieSchema.model_validate(movie) for movie in movie_list]

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    return {
        "movies": movies,
        "prev_page": f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        "next_page": f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


def create_movie(movie_data, db: Session = Depends(get_db)):
    if not 0 <= movie_data.score <= 100:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie_data.budget < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie_data.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing_movie = db.query(MovieModel).filter_by(name=movie_data.name, date=movie_data.date).first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and"
                   f" release date '{movie_data.date}' already exists."
        )

    country = db.query(CountryModel).filter_by(code=movie_data.country).first()
    if not country:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for genre_name in movie_data.genres:
        genre = db.query(GenreModel).filter_by(name=genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.commit()
            db.refresh(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = db.query(ActorModel).filter_by(name=actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.commit()
            db.refresh(actor)
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = db.query(LanguageModel).filter_by(name=language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.commit()
            db.refresh(language)
        languages.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(movie)
    db.commit()
    db.refresh(movie)

    return get_movie(movie.id, db)


def delete_movie(movie_id: int, db: Session):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    db.delete(movie)
    db.commit()
    return movie


def update_movie(movie_id: int, movie_data: MovieUpdate, db: Session):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    if movie_data.score and not 0 < movie_data.score < 100:
        raise HTTPException(
            status_code=400, detail="Invalid input data."
        )
    if movie_data.budget and movie_data.budget < 0:
        raise HTTPException(
            status_code=400, detail="Invalid input data."
        )
    if movie_data.revenue and movie_data.revenue < 0:
        raise HTTPException(
            status_code=400, detail="Invalid input data."
        )
    if movie_data.name and movie_data.date:
        if db.query(MovieModel).filter_by(name=movie_data.name, date=movie_data.date).first() is not None:
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{movie.name}'"
                       f" and release date '{movie.date}' already exists."
            )

    if movie_data.name:
        movie.name = movie_data.name
    if movie_data.date:
        movie.date = movie_data.date
    if movie_data.score:
        movie.score = movie_data.score
    if movie_data.overview:
        movie.overview = movie_data.overview
    if movie_data.status:
        movie.status = movie_data.status
    if movie_data.budget:
        movie.budget = movie_data.budget
    if movie_data.revenue:
        movie.revenue = movie_data.revenue

    db.commit()
    db.refresh(movie)

    return {"detail": "Movie updated successfully."}
