import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from starlette import status

from schemas.movies import MovieListPaginated, MovieDetail, MovieUpdate, MovieCreate

router = APIRouter()


@router.get("/movies/", response_model=MovieListPaginated)
def get_movies(
        page: int = Query(ge=1, default=1),
        per_page: int = Query(ge=1, le=20, default=10),
        db: Session = Depends(get_db),
):
    movie = db.query(MovieModel)
    total_items = movie.count()
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page
    movies = movie.order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={max(1, page - 1)}&per_page={per_page}" if page > 1 else None
    next_page = (f"/theater/movies/?page={min(total_pages, page + 1)}"
                 f"&per_page={per_page}") if page < total_pages else None

    movies_list = []
    for movie in movies:
        try:
            validated_movie = MovieModel.model_validate(movie)
            movies_list.append(validated_movie)
        except AttributeError as e:
            raise HTTPException(status_code=500, detail=f"Error validating movie: {e}")

    result = MovieListPaginated(
        movies=movies_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )

    return result


@router.get("movies/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/movies/", response_model=MovieDetail, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    if (
            len(movie.name) > 255
            or movie.date > date.today() + timedelta(days=365)
            or not (0 <= movie.score <= 100)
            or movie.budget < 0
            or movie.revenue < 0
    ):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    ).first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for genre_id in movie.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_id).first()
        if not genre:
            genre = GenreModel(name=genre_id)
            db.add(genre)
            db.commit()
            db.refresh(genre)
        genres.append(genre)

    actors = []
    for actor_id in movie.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_id).first()
        if not actor:
            actor = ActorModel(name=actor_id)
            db.add(actor)
            db.commit()
            db.refresh(actor)
        actors.append(actor)

    languages = []
    for language_id in movie.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_id).first()
        if not language:
            language = LanguageModel(name=language_id)
            db.add(language)
            db.commit()
            db.refresh(language)
        languages.append(language)

    new_movie_data = movie.dict(exclude={"country", "genres", "actors", "languages"})
    new_movie = MovieModel(country=country, **new_movie_data)

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    new_movie.genres.extend(genres)
    new_movie.actors.extend(actors)
    new_movie.languages.extend(languages)
    db.commit()

    return new_movie


@router.patch("movies/{movie_id}")
def patch_movie(movie_id, movie: MovieUpdate, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if (
            not (0 <= movie.score <= 100)
            or (movie.budget is not None and movie.budget < 0)
            or (movie.revenue is not None and movie.revenue < 0)
    ):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie.name is not None:
        db_movie.name = movie.name
    if movie.date is not None:
        db_movie.date = movie.date
    if movie.score is not None:
        db_movie.score = movie.score
    if movie.overview is not None:
        db_movie.overview = movie.overview
    if movie.status is not None:
        db_movie.status = movie.status
    if movie.budget is not None:
        db_movie.budget = movie.budget
    if movie.revenue is not None:
        db_movie.revenue = movie.revenue

    db.commit()
    db.refresh(db_movie)
    return {
        "detail": "Movie updated successfully."
    }


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first().delete()

    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(db_movie)
    db.commit()
