import math

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from sqlalchemy.orm import Session

from crud.movies import get_movies, create_movie, get_movie, delete_movie, update_movie
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
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    MoviePageSchema,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

router = APIRouter()


@router.post("/movies", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):

    existing_film = (
        db.query(MovieModel)
        .filter(MovieModel.name == movie.name, MovieModel.date == movie.date)
        .first()
    )

    if existing_film:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    try:
        country = db.query(CountryModel).filter_by(code=movie.country).first()

        if not country:
            country = CountryModel(code=movie.country)
            db.add(country)
            db.flush()

        genres = []
        for genre in movie.genres:
            genre_exist = db.query(GenreModel).filter_by(name=genre).first()
            if not genre_exist:
                genre_new = GenreModel(name=genre)
                db.add(genre_new)
                db.flush()
                genre_exist = genre_new
            genres.append(genre_exist)

        actors = []
        for actor in movie.actors:
            actor_exist = db.query(ActorModel).filter_by(name=actor).first()
            if not actor_exist:
                actor_new = ActorModel(name=actor)
                db.add(actor_new)
                db.flush()
                actor_exist = actor_new
            actors.append(actor_exist)

        languages = []
        for language in movie.languages:
            language_exist = db.query(LanguageModel).filter_by(name=language).first()
            if not language_exist:
                language_new = LanguageModel(name=language)
                db.add(language_new)
                db.flush()
                language_exist = language_new
            languages.append(language_exist)

        movie = MovieModel(
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
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return MovieDetailSchema.model_validate(movie)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data!")


@router.get("/movies", response_model=None)
async def get_list_movie(
    page: int = Query(1, ge=1, description="Page must be more than 1"),
    per_page: int = Query(
        10, ge=1, le=20, description="Items per page can be in diapason 1-20"
    ),
    db: Session = Depends(get_db),
):
    sorted_movies = db.query(MovieModel).order_by(MovieModel.id.desc())
    total_items = sorted_movies.count()
    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = sorted_movies.offset((page - 1) * per_page).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [MovieListItemSchema.model_validate(movie) for movie in movies]

    previous_page = None if page <= 1 else page - 1
    next_page = None if page >= total_pages else page + 1
    return MovieListResponseSchema(
        movies=movie_list,
        prev_page=(
            f"/theater/movies/?page={previous_page}&per_page={per_page}"
            if previous_page
            else None
        ),
        next_page=(
            f"/theater/movies/?page={next_page}&per_page={per_page}"
            if next_page
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_detail_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = (
        db.query(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .filter(MovieModel.id == movie_id)
        .first()
    )

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", response_model=None, status_code=204)
async def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    db.delete(movie)
    db.commit()
    return {"detail": "Movie deleted successfully!", "status_code": 204}


@router.patch("/movies/{movie_id}/", response_model=None)
async def update_movie(
    movie_id: int, movie_data: MovieUpdateSchema, db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        db.commit()
        db.refresh(movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    else:
        return {"detail": "Movie updated successfully."}
