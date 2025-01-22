from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    PaginatedMoviesSchema,
    CountrySchema,
    GenreSchema,
    ActorSchema,
    LanguageSchema,
    MovieListItemSchema
)

router = APIRouter()


@router.get("/movies/", response_model=PaginatedMoviesSchema)
def get_movies(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    query = db.query(MovieModel).order_by(MovieModel.id.desc())
    total_items = query.count()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    def create_movie_schema(movie: MovieModel) -> MovieListItemSchema:
        return MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
        )

    movie_list = [create_movie_schema(movie) for movie in movies]

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return PaginatedMoviesSchema(
        movies=movie_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieSchema, status_code=201)
def create_movie(movie_data: MovieCreateSchema, db: Session = Depends(get_db)):
    if db.query(MovieModel).filter(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date).first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country = db.query(CountryModel).filter_by(code=movie_data.country).first()
    if not country:
        country = CountryModel(code=movie_data.country, name=None)
        db.add(country)
        db.flush()

    genres = []
    for genre_name in movie_data.genres:
        genre = db.query(GenreModel).filter_by(name=genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.flush()
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = db.query(ActorModel).filter_by(name=actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.flush()
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = db.query(LanguageModel).filter_by(name=language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.flush()
        languages.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(movie)
    db.commit()
    db.refresh(movie)

    return MovieSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=CountrySchema(
            id=movie.country.id,
            code=movie.country.code,
            name=movie.country.name
        ),
        genres=sorted([GenreSchema(id=genre.id, name=genre.name) for genre in movie.genres], key=lambda x: x.id),
        actors=sorted([ActorSchema(id=actor.id, name=actor.name) for actor in movie.actors], key=lambda x: x.id),
        languages=sorted([LanguageSchema(id=language.id, name=language.name) for language in movie.languages],
                         key=lambda x: x.id)
    )


@router.get("/movies/{movie_id}/", response_model=MovieSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=CountrySchema(
            id=movie.country.id,
            code=movie.country.code,
            name=movie.country.name
        ),
        genres=sorted([GenreSchema(id=genre.id, name=genre.name) for genre in movie.genres], key=lambda x: x.id),
        actors=sorted([ActorSchema(id=actor.id, name=actor.name) for actor in movie.actors], key=lambda x: x.id),
        languages=sorted([LanguageSchema(id=language.id, name=language.name) for language in movie.languages],
                         key=lambda x: x.id)
    )


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(movie)
    db.commit()


@router.patch("/movies/{movie_id}/")
def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: Session = Depends(get_db),
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for key, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.") from e

    return {"detail": "Movie updated successfully."}
