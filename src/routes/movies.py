from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    PaginationPages,
    MovieRead,
    MovieCreate,
    MovieUpdate,
)

router = APIRouter()


@router.get("/movies/", response_model=PaginationPages)
def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: Session = Depends(get_db)
):
    skip = (page - 1) * per_page
    limit = per_page

    movie_query = db.query(MovieModel).order_by(MovieModel.id.desc())
    total_items = movie_query.count()
    db_movies = movie_query.offset(skip).limit(limit).all()
    if not db_movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_pages = ceil(total_items / per_page)

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return PaginationPages(
        movies=db_movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


def get_or_create_genre(genre: str, db: Session = Depends(get_db)):
    db_genre = db.query(GenreModel).filter(GenreModel.name == genre).first()
    if not db_genre:
        db_genre = GenreModel(name=genre)
        db.add(db_genre)
        db.commit()
        db.refresh(db_genre)

    return db_genre


def get_or_create_actor(actor: str, db: Session = Depends(get_db)):
    db_actor = db.query(ActorModel).filter(ActorModel.name == actor).first()
    if not db_actor:
        db_actor = ActorModel(name=actor)
        db.add(db_actor)
        db.commit()
        db.refresh(db_actor)

    return db_actor


def get_or_create_country(country: str, db: Session = Depends(get_db)):
    db_country = db.query(CountryModel).filter(CountryModel.code == country).first()
    if not db_country:
        db_country = CountryModel(code=country)
        db.add(db_country)
        db.commit()
        db.refresh(db_country)

    return db_country


def get_or_create_language(language: str, db: Session = Depends(get_db)):
    db_language = db.query(LanguageModel).filter(LanguageModel.name == language).first()
    if not db_language:
        db_language = LanguageModel(name=language)
        db.add(db_language)
        db.commit()
        db.refresh(db_language)

    return db_language


@router.post("/movies/", response_model=MovieRead, status_code=201)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = get_or_create_country(movie.country, db)

    genres = []
    for genre_name in movie.genres:
        genre = get_or_create_genre(genre_name, db)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = get_or_create_actor(actor_name, db)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = get_or_create_language(language_name, db)
        languages.append(language)

    db_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
    )

    db_movie.genres = genres
    db_movie.actors = actors
    db_movie.languages = languages
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)

    return db_movie


@router.get("/movies/{movie_id}/", response_model=MovieRead)
def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).filter(MovieModel.id == movie_id).first()

    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieRead(
        id=db_movie.id,
        name=db_movie.name,
        date=db_movie.date,
        score=db_movie.score,
        overview=db_movie.overview,
        status=db_movie.status,
        budget=db_movie.budget,
        revenue=db_movie.revenue,
        country={
            "id": db_movie.country.id,
            "code": db_movie.country.code,
            "name": db_movie.country.name if db_movie.country.name else None
        },
        genres=[{"id": genre.id, "name": genre.name} for genre in db_movie.genres],
        actors=[{"id": actor.id, "name": actor.name} for actor in db_movie.actors],
        languages=[{"id": language.id, "name": language.name} for language in db_movie.languages]
    )


@router.delete("/movies/{movie_id}/")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(db_movie)
    db.commit()

    return Response(status_code=204)


@router.patch("/movies/{movie_id}/", status_code=200)
def update_movie(movie_id, movie: MovieUpdate, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    if movie.name:
        db_movie.name = movie.name

    if movie.date:
        db_movie.date = movie.date

    if movie.score is not None:
        if not (0 <= movie.score <= 100):
            raise HTTPException(status_code=400, detail="Invalid input data.")
        db_movie.score = movie.score

    if movie.overview:
        db_movie.overview = movie.overview

    if movie.status:
        db_movie.status = movie.status

    if movie.budget is not None:
        if movie.budget < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        db_movie.budget = movie.budget

    if movie.revenue is not None:
        if movie.revenue < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        db_movie.revenue = movie.revenue

    db.commit()
    db.refresh(db_movie)

    return {"detail": "Movie updated successfully."}
