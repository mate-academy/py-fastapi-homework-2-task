from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.schemas.movies import MovieCreate, MovieResponse
from src.database.models import MovieModel, GenreModel, ActorModel, CountryModel, LanguageModel

router = APIRouter()


@router.get("/movies/", response_model=MovieResponse)
async def get_movies(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    # Расчет пагинации
    offset = (page - 1) * per_page
    movies_query = db.query(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    movies = movies_query.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_movies = db.query(MovieModel).count()
    total_pages = (total_movies + per_page - 1) // per_page

    prev_page = f"/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_movies
    }

router = APIRouter()

@router.post("/movies/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie: MovieCreate, db: Session = Depends(get_db)
):
    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).first()

    if existing_movie:
        raise HTTPException(status_code=409, detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.")

    new_movie = MovieModel(**movie.dict())

    for genre_name in movie.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if genre is None:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        new_movie.genres.append(genre)

    for actor_name in movie.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if actor is None:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        new_movie.actors.append(actor)

    country = db.query(CountryModel).filter(CountryModel.name == movie.country).first()
    if country is None:
        country = CountryModel(name=movie.country)
        db.add(country)
    new_movie.country = country

    for language_name in movie.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
        if language is None:
            language = LanguageModel(name=language_name)
            db.add(language)
        new_movie.languages.append(language)

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return new_movie

@router.get("/movies/{movie_id}/", response_model=MovieResponse)
async def get_movie_details(
    movie_id: int, db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie
