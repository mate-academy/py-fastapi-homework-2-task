import datetime
from datetime import date
from typing import Type

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import MovieModel
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel, Base
from schemas.movies import MovieCreateRequestSchema, MovieUpdateRequestSchema, MovieListSchema, \
    MovieCreateResponseSchema


def get_all_movies(db: Session, page: int, per_page: int) -> MovieListSchema:
    start = (page - 1) * per_page
    movies = db.query(MovieModel).order_by(
        MovieModel.id.desc()
    ).offset(start).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MovieListSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )

# ---------------------------------------------------------------------------------

# def check_data(
#         db: Session,
#         input_data: list[str],
#         model: Type[Base]
# ) -> list[Type[Base]]:
#     results = []
#
#     for data in input_data:
#         item = db.query(model).filter(model.name == data).first()
#
#         if not item:
#             item = model(name=data)
#             db.add(item)
#             db.commit()
#             db.refresh(item)
#
#         results.append(item)
#
#     return results



def create_movie(movie_data: MovieCreateRequestSchema, db: Session) -> MovieModel:
    """Creates new movie record with all related entities."""
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


def get_movie_by_id(movie_id: int, db: Session) -> MovieModel | None:
    return db.query(MovieModel).filter(MovieModel.id == movie_id).first()


def get_movie_by_name_and_date(name: str, date: date, db: Session) -> MovieModel | None:
    return db.query(MovieModel).filter(MovieModel.name == name, MovieModel.date == date).first()




# ---------------------------------------------------------------------------------
def update_movie(movie: MovieModel, movie_data: MovieUpdateRequestSchema, db: Session) -> MovieModel:
    update_data = movie_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    db.commit()
    db.refresh(movie)

    return movie

def delete_movie(movie: MovieModel, db: Session) -> None:
    db.delete(movie)
    db.commit()


