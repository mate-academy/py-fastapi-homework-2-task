from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieListResponseSchema, MovieCreateSchema, MovieDetailResponseSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
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

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieCreateSchema, status_code=201)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):
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

    def get_or_create(model, db, **kwargs):
        instance = db.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            db.add(instance)
            db.flush()
        return instance

    country = get_or_create(CountryModel, db, code=movie.country)
    genres = [get_or_create(GenreModel, db, name=genre_name) for genre_name in movie.genres]
    actors = [get_or_create(ActorModel, db, name=actor_name) for actor_name in movie.actors]
    languages = [get_or_create(LanguageModel, db, name=language_name) for language_name in movie.languages]

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

    return MovieCreateSchema(
        id=new_movie.id,
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


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
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


@router.patch("/movies/{movie_id}/", status_code=200)
def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    movie.name = movie_data.name if movie_data.name else movie.name
    movie.date = movie_data.date if movie_data.date else movie.date
    movie.score = movie_data.score if movie_data.score else movie.score
    movie.overview = movie_data.overview if movie_data.overview else movie.overview
    movie.status = movie_data.status if movie_data.status else movie.status
    movie.budget = movie_data.budget if movie_data.budget else movie.budget
    movie.revenue = movie_data.revenue if movie_data.revenue else movie.revenue

    db.commit()

    return {"detail": "Movie updated successfully."}
