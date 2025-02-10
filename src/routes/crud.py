from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import MovieModel
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import MovieCreate, MovieUpdate


def get_movies(db: Session):
    return db.query(MovieModel).all()