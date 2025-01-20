import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateOptional

from src.schemas.movies import MovieResponse, MovieCreateResponse, MovieCreateRequest, \
    MovieBase

router = APIRouter()


@router.post("/movies/", response_model=MovieCreateResponse, status_code=201)
async def create_movie(movie_data: MovieCreateRequest, db: Session = Depends(get_db)):
    if movie_data.score < 0 or movie_data.score > 100:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100.")

    if movie_data.budget < 0 or movie_data.revenue < 0:
        raise HTTPException(status_code=400, detail="Budget and revenue must be non-negative.")

    if len(movie_data.name) > 255:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if movie_data.date > datetime.datetime.now().date() + datetime.timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    ).first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name "
            f"'{movie_data.name}' and release date "
            f"'{movie_data.date}' already exists."
        )

    country = db.query(CountryModel).filter(CountryModel.code == movie_data.country).first()

    if not country:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for genre_name in movie_data.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.commit()
            db.refresh(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie_data.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.commit()
            db.refresh(actor)
        actors.append(actor)

    languages = []
    for language_name in movie_data.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
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
    try:
        db.commit()
        db.refresh(movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error creating movie.")

    return movie


@router.get("/movies/", response_model=MovieResponse)
def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: Session = Depends(get_db)
):
    skip = (page - 1) * per_page

    movies = db.query(MovieModel).order_by(desc(MovieModel.id)).offset(skip).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = db.query(MovieModel).count()

    if total_items % per_page == 0:
        total_pages = total_items // per_page
    else:
        total_pages = (total_items // per_page) + 1

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    movie_details = [MovieBase.model_validate(movie) for movie in movies]

    return MovieResponse(
        movies=movie_details,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get("/movies/{movie_id}/", response_model=MovieCreateResponse)
async def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(movie)
    db.commit()
    return {"detail": "Movie deleted successfully."}


@router.patch("/movies/{movie_id}/")
def update_movie(movie_id: int, movie: MovieCreateOptional, db: Session = Depends(get_db)):
    movie_obj = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie_obj:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for field, value in movie.dict(exclude_unset=True).items():
        setattr(movie_obj, field, value)

    db.commit()
    db.refresh(movie_obj)
    return {"detail": "Movie updated successfully."}
