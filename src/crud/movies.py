from datetime import date

from sqlalchemy.orm import Session

from database import MovieModel
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import MovieCreateRequestSchema, MovieUpdateRequestSchema


def get_movies_with_pagination(offset: int, per_page: int, db: Session) -> tuple[list[MovieModel], int]:
    """Retrieves paginated movies from database by ID descending."""
    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()
    movies_count = db.query(MovieModel).count()

    return movies, movies_count


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
    """Retrieves single movie by ID."""
    return db.query(MovieModel).filter(MovieModel.id == movie_id).first()


def get_movie_by_name_and_date(name: str, date: date, db: Session) -> MovieModel | None:
    """
    Checks if movie with given name and date exists.

    Used for duplicate checking during creation.
    """
    return db.query(MovieModel).filter(MovieModel.name == name, MovieModel.date == date).first()


def delete_movie(movie: MovieModel, db: Session) -> None:
    """Deletes movie and all its relationships."""
    db.delete(movie)
    db.commit()


def update_movie(movie: MovieModel, movie_data: MovieUpdateRequestSchema, db: Session) -> MovieModel:
    """Updates movie with partial data."""
    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    db.commit()
    db.refresh(movie)

    return movie
