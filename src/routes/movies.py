from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieList, MovieCreate, MovieDetail

router = APIRouter()


@router.get("/movies/", response_model=MovieList)
def get_movies_list(
        page: int = Query(1, ge=1, description="Page number, must be >= 1"),
        per_page: int = Query(
            10, ge=1, le=20,
            description="Items per page, must be >= 1 and <= 20"
        ),
        db: Session = Depends(get_db)
):
    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    movies = (
        db.query(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (f"/theater/movies/?page={page - 1}"
                 f"&per_page={per_page}") if page > 1 else None
    next_page = (f"/theater/movies/?page={page + 1}"
                 f"&per_page={per_page}") if page < total_pages else None

    return MovieList(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieCreate, status_code=201)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    if len(movie.name) > 255:
        raise HTTPException(status_code=400, detail="Name must not exceed 255 characters.")
    if movie.date > (date.today() + timedelta(days=365)):
        raise HTTPException(status_code=400, detail="Date cannot be more than one year in the future.")
    if not (0 <= movie.score <= 100):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100.")
    if movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Budget and revenue must be non-negative.")

    existing_movie = db.query(MovieModel).filter_by(name=movie.name, date=movie.date).first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = db.query(CountryModel).filter_by(code=movie.country).first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        db.flush()

    genres = []
    for genre_name in movie.genres:
        genre = db.query(GenreModel).filter_by(name=genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.flush()
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = db.query(ActorModel).filter_by(name=actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.flush()
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = db.query(LanguageModel).filter_by(name=language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.flush()
        languages.append(language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return MovieCreate(
        name=new_movie.name,
        date=new_movie.date,
        score=new_movie.score,
        overview=new_movie.overview,
        status=new_movie.status,
        budget=new_movie.budget,
        revenue=new_movie.revenue,
        country=new_movie.country.code,
        genres=[genre.name for genre in new_movie.genres],
        actors=[actor.name for actor in new_movie.actors],
        languages=[language.name for language in new_movie.languages],
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    db.delete(movie)
    db.commit()
    return None
