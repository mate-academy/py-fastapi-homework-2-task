import math
from datetime import timedelta, date
from typing import Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, JSONResponse

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel, Base
from routes.utils import get_or_404, extract
from schemas.movies import MovieDetailSchema, MovieListResponseSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter()

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10
ROOT = "/theater"


@router.get("/movies/", response_model=MovieListResponseSchema)
def list_movies(
        page: int = Query(DEFAULT_PAGE, ge=1),
        per_page: int = Query(DEFAULT_PER_PAGE, ge=1, le=20),
        db: Session = Depends(get_db),
):

    offset = (page - 1) * per_page
    total_items = db.query(MovieModel).count()
    total_pages = math.ceil(total_items / per_page)

    next_page = f"{ROOT}/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    prev_page = f"{ROOT}/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None

    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).limit(per_page).offset(offset).all()

    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> Type[MovieModel]:
    movie = get_or_404(movie_id, MovieModel, db)
    return movie


@router.delete("/movies/{movie_id}/", response_model=None)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> Response:
    db_movie = get_or_404(movie_id, MovieModel, db)
    try:
        db.delete(db_movie)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error. " + str(e))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/", response_model=None, status_code=status.HTTP_200_OK)
def update_movie(movie_id: int, movie_update: MovieUpdateSchema, db: Session = Depends(get_db)) -> dict:
    db_movie = get_or_404(movie_id, MovieModel, db)

    # for all schema fields: update model fields only if value is not none
    for field_name, field_value in movie_update.model_dump(exclude_unset=True).items():
        print(f"Field {field_name}: {field_value}")
        if field_value is not None:
            setattr(db_movie, field_name, field_value)

    try:
        db.commit()
        db.refresh(db_movie)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SQLAlchemyError: " + str(e))

    return {"detail": "Movie updated successfully."}

@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
def create_movie(
        movie: MovieCreateSchema,
        db: Session = Depends(get_db),
) -> MovieModel:

    if not(0 < movie.score < 100) or movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data. Movie score out of range (0,100) or budget or revenue must be positive."
        )
    if movie.date > date.today() + timedelta(days=365):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data. Date cannot be in so far the future."
        )
    if len(movie.name) > 255 or len(movie.country) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data. Movie name or country code too long."
        )

    db_movie = db.query(MovieModel).filter(MovieModel.name == movie.name, MovieModel.date == movie.date).first()
    if db_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    if not country:
        country = CountryModel(code=movie.country)
        try:
            db.add(country)
            db.commit()
            db.refresh(country)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database Error. " + str(e))

    genres = extract(movie.genres, GenreModel, db)
    actors = extract(movie.actors, ActorModel, db)
    languages = extract(movie.languages, LanguageModel, db)

    # add only movie data + country
    db_movie = MovieModel(**movie.model_dump(exclude={"country", "genres", "actors", "languages"}), country=country)
    try:
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error. " + str(e))

    # add relations with 'genres, 'actors, 'languages
    db_movie.genres.extend(genres)
    db_movie.actors.extend(actors)
    db_movie.languages.extend(languages)
    db.commit()

    return db_movie
