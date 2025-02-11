from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetail,
    MovieCreate,
    MovieUpdate
)

from database import get_db
from database.models import MovieModel
from crud import (
    get_movies_on_page,
    get_movie_by_id,
    get_or_create_country,
    get_or_create_actor,
    get_or_create_genre,
    get_or_create_language,
    create_new_movie
)

router = APIRouter()


@router.get("/movies", response_model=MovieListResponseSchema)
def get_movies(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    movies = get_movies_on_page(page, per_page, db)
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = db.query(MovieModel).count()
    total_pages = (total_items // per_page) + (
        1 if total_items % per_page > 0
        else 0
    )

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    return {
        "movies": movies,
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page != 1
            else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}", response_model=MovieDetail)
def get_movie_detail(movie_id: int, db: Session = Depends(get_db)):
    movie = get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.post("/movies", response_model=MovieDetail, status_code=201)
def add_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).first()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    country = get_or_create_country(db, movie.country)
    genres = [get_or_create_genre(db, genre) for genre in movie.genres]
    actors = [
        get_or_create_actor(db, actor_name) for actor_name in movie.actors
    ]
    languages = [
        get_or_create_language(db, language) for language in movie.languages
    ]

    try:
        new_film = MovieModel(
            **movie.model_dump(
                exclude={"country", "genres", "actors", "languages"}
            ),
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        return create_new_movie(new_film, db)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete("/movies/{movie_id}", response_model=MovieDetail)
def remove_film(movie_id: int, db: Session = Depends(get_db)):
    db_film = get_movie_by_id(db, movie_id)
    if not db_film:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    db.delete(db_film)
    db.commit()
    return Response(status_code=204)


@router.patch("/movies/{movie_id}", response_model=MovieDetail)
def update_film(
        movie_id: int,
        movie: MovieUpdate,
        db: Session = Depends(get_db)
):
    db_film = get_movie_by_id(db, movie_id)
    if not db_film:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    db_film.name = movie.name
    db_film.date = movie.date if movie.date is not None else db_film.date
    db_film.score = (
        movie.score if movie.score is not None
        else db_film.score
    )
    db_film.overview = (
        movie.overview
        if movie.overview is not None
        else db_film.overview
    )
    db_film.status = (
        movie.status if movie.status is not None
        else db_film.status
    )
    db_film.budget = (
        movie.budget if movie.budget is not None
        else db_film.budget
    )
    db_film.revenue = (
        movie.revenue if movie.revenue is not None
        else db_film.revenue
    )
    db.commit()
    db.refresh(db_film)
    return JSONResponse(content={"detail": "Movie updated successfully."})
