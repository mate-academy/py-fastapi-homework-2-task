from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)

from schemas.movies import (
    MovieListSchema,
    MovieCreateResponse,
    MovieCreateRequest,
)

from schemas.movies import MovieUpdate

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Hello World"}


@router.get("/movies", response_model=MovieListSchema)
def list_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * per_page
    movies = (
        db.query(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    if page == 1:
        prev_page = None

    if page == total_pages:
        next_page = None

    return MovieListSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieCreateResponse,
)
def add_movie(movie: MovieCreateRequest, db: Session = Depends(get_db)):
    existing_movie = (
        db.query(MovieModel)
        .filter(MovieModel.name == movie.name, MovieModel.date == movie.date)
        .first()
    )
    if existing_movie:
        raise HTTPException(
            409,
            f"A movie with the name '{movie.name}' "
            f"and release date '{movie.date}' already exists.",
        )

    country = (
        db.query(CountryModel)
        .filter(CountryModel.code == movie.country)
        .first()
    )

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for name in movie.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == name).first()
        if genre:
            genres.append(genre)
        else:
            new_genre = GenreModel(name=name)
            db.add(new_genre)
            db.commit()
            db.refresh(new_genre)
            genres.append(new_genre)

    languages = []
    for name in movie.languages:
        language = (
            db.query(LanguageModel).filter(LanguageModel.name == name).first()
        )
        if language:
            languages.append(language)
        else:
            new_language = LanguageModel(name=name)
            db.add(new_language)
            db.commit()
            db.refresh(new_language)
            languages.append(new_language)

    actors = []
    for name in movie.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == name).first()
        if actor:
            actors.append(actor)
        else:
            new_actor = ActorModel(name=name)
            db.add(new_actor)
            db.commit()
            db.refresh(new_actor)
            actors.append(new_actor)

    new_movie = MovieModel(
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

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie


@router.get("/movies/{movie_id}/", response_model=MovieCreateResponse)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    existing_movie = (
        db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    )

    if not existing_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return existing_movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def remove_film(movie_id: int, db: Session = Depends(get_db)):
    existing_movie = (
        db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    )

    if not existing_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    db.delete(existing_movie)
    db.commit()


@router.patch("/movies/{movie_id}/")
def edit_movie(
    movie: MovieUpdate, movie_id: int, db: Session = Depends(get_db)
):
    existing_movie = (
        db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    )

    if not existing_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    if movie.name:
        existing_movie.name = movie.name

    if movie.date:
        existing_movie.date = movie.date

    if movie.score:
        existing_movie.score = movie.score

    if movie.overview:
        existing_movie.overview = movie.overview

    if movie.status:
        existing_movie.status = movie.status

    if movie.budget:
        existing_movie.budget = movie.budget

    if movie.revenue:
        existing_movie.revenue = movie.revenue

    db.commit()
    db.refresh(existing_movie)
    return {"detail": "Movie updated successfully.", "movie": existing_movie}
