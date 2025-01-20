from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
import datetime
from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)

from schemas.movies import MovieListResponse, MovieDetail, MovieCreate, MovieUpdate

from crud import (
    create_country_by_code,
    create_instance_by_name,
    check_or_create_many_instances_by_name,
    get_movies_on_page,
    get_movie_by_name_and_date,
    get_movie_by_id,
)

from src.crud import create_new_movie

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponse)
def get_movies(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
) -> MovieListResponse:

    movies = get_movies_on_page(page, per_page, MovieModel, db)

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"
    total_items = db.query(MovieModel).count()
    total_pages = (total_items // per_page) + (1 if total_items % per_page > 0 else 0)

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found")

    return {
        "movies": movies,
        "prev_page": prev_page if page > 1 else None,
        "next_page": next_page if total_pages > page else None,
        "total_items": total_items,
        "total_pages": total_pages,
    }


@router.post("/movies/", response_model=MovieDetail, status_code=201)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)) -> MovieDetail:
    db_movie = get_movie_by_name_and_date(
        name=movie.name, date=movie.date, model=MovieModel, db=db
    )

    if db_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{db_movie.name}' and release date '{db_movie.date}' already exists.",
        )

    if movie.date > datetime.datetime.now().date() + datetime.timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    genres = []
    actors = []
    languages = []

    if movie.languages:
        languages.extend(
            check_or_create_many_instances_by_name(movie.languages, LanguageModel, db)
        )

    if movie.actors:
        actors.extend(
            check_or_create_many_instances_by_name(movie.actors, ActorModel, db)
        )

    if movie.genres:
        genres.extend(
            check_or_create_many_instances_by_name(movie.genres, GenreModel, db)
        )

    if not country:
        country = create_country_by_code(code=movie.country, model=CountryModel, db=db)

    try:
        new_movie = MovieModel(
            **movie.model_dump(exclude={"country", "genres", "actors", "languages"}),
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        return create_new_movie(movie=new_movie, db=db)

    except IntegrityError:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetail:
    movie = get_movie_by_id(movie_id, MovieModel, db)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> None:
    movie = get_movie_by_id(movie_id, MovieModel, db)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    db.delete(movie)
    db.commit()


@router.patch("/movies/{movie_id}/", status_code=200)
def edit_movie(
    movie_id: int, movie_data: MovieUpdate, db: Session = Depends(get_db)
) -> dict[str, str]:
    movie = get_movie_by_id(movie_id, MovieModel, db)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    try:
        movie_date = movie_data.model_dump(exclude_unset=True)
        for key, value in movie_date.items():
            if value:
                setattr(movie, key, value)
        db.commit()
        db.refresh(movie)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
