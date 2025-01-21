import datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy.orm import Session

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieDetailResponseSchema,
    MovieListResponseSchema,
    MovieUpdateResponseSchema,
    MovieCreateResponseSchema,
    MovieListReadResponseSchema
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
def get_movies(
    page: Annotated[int, Query(ge=1, description="The page number to fetch.")] = 1,
    per_page: Annotated[int, Query(ge=1, le=20, description="Number of movies per page.")] = 10,
    db: Session = Depends(get_db)
):
    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages or total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    movies_query = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page).all()
    movies = [MovieListReadResponseSchema.model_validate(movie) for movie in movies_query]

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}", response_model=MovieDetailResponseSchema)
def get_movie_by_id(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreateResponseSchema, db: Session = Depends(get_db)):
    if len(movie.name) > 255:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if movie.date > datetime.datetime.now().date() + datetime.timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if not (0 <= movie.score <= 100):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    if movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

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
        db.commit()
        db.refresh(country)

    genres = []
    for genre in movie.genres:
        genre_obj = db.query(GenreModel).filter_by(name=genre).first()
        if not genre_obj:
            genre_obj = GenreModel(name=genre)
            db.add(genre_obj)
            db.commit()
            db.refresh(genre_obj)
        genres.append(genre_obj)

    actors = []
    for actor in movie.actors:
        actor_obj = db.query(ActorModel).filter_by(name=actor).first()
        if not actor_obj:
            actor_obj = ActorModel(name=actor)
            db.add(actor_obj)
            db.commit()
            db.refresh(actor_obj)
        actors.append(actor_obj)

    languages = []
    for language in movie.languages:
        language_obj = db.query(LanguageModel).filter_by(name=language).first()
        if not language_obj:
            language_obj = LanguageModel(name=language)
            db.add(language_obj)
            db.commit()
            db.refresh(language_obj)
        languages.append(language_obj)

    db_movie = MovieModel(
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

    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(db_movie)
    db.commit()


@router.patch("/movies/{movie_id}")
def edit_movie(movie_id: int, movie: MovieUpdateResponseSchema, db: Session = Depends(get_db)):
    db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie.name:
        if len(movie.name) > 255:
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )
        db_movie.name = movie.name

    if movie.date:
        if movie.date > datetime.datetime.now().date() + datetime.timedelta(days=365):
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )
        db_movie.date = movie.date

    if movie.score:
        if not (0 <= movie.score <= 100):
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )
        db_movie.score = movie.score

    if movie.overview:
        db_movie.overview = movie.overview
    if movie.status:
        db_movie.status = movie.status

    if movie.budget:
        if movie.budget < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )
        db_movie.budget = movie.budget

    if movie.revenue:
        if movie.revenue < 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid input data."
            )
        db_movie.revenue = movie.revenue

    db.commit()
    db.refresh(db_movie)
    return {"detail": "Movie updated successfully.", "movie": db_movie}
