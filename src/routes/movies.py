from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListSchema, MovieCreateSchema, MovieDetailSchema, MovieUpdateSchema, MovieResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListSchema)
def get_list_movies(page: int = Query(default=1, ge=1),
                    per_page: int = Query(default=10, ge=1, le=20),
                    db: Session = Depends(get_db)) -> list[MovieListSchema]:
    movies = (db.query(MovieModel).order_by(MovieModel.id.desc()).offset((page - 1) * per_page).limit(per_page).all())

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < 20:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    return MovieListSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )

@router.post("/movies/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)) -> MovieResponseSchema:
    movie_check = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).count()
    if movie_check > 0:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = db.query(CountryModel).filter_by(code=movie.country).first()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = [
        db.query(GenreModel).filter(GenreModel.name == name).first() or GenreModel(name=name)
        for name in movie.genres
    ]
    for genre in genres:
        db.add(genre)
    db.commit()

    actors = [
        db.query(ActorModel).filter(ActorModel.name == name).first() or ActorModel(name=name)
        for name in movie.actors
    ]
    for actor in actors:
        db.add(actor)
    db.commit()

    languages = [
        db.query(LanguageModel).filter(LanguageModel.name == name).first() or LanguageModel(name=name)
        for name in movie.languages
    ]
    for language in languages:
        db.add(language)
    db.commit()

    new_movie = MovieModel(
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

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return MovieResponseSchema.model_validate(new_movie)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
def get_movie_by_id(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailSchema:
    movie = db.query(MovieModel).filter(MovieModel.id==movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", response_model=None)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id==movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(movie)
    db.commit()

    return Response(status_code=204)


@router.patch("/movies/{movie_id}/")
def update_movie(movie_id: int, new_movie: MovieUpdateSchema, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if new_movie.score is not None and (new_movie.score < 0 or new_movie.score > 100):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100.")

    if new_movie.budget is not None and new_movie.budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative.")

    if new_movie.revenue is not None and new_movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Revenue must be non-negative.")

    if new_movie.name:
        movie.name = new_movie.name
    if new_movie.date:
        movie.date = new_movie.date
    if new_movie.score:
        movie.score = new_movie.score
    if new_movie.overview:
        movie.overview = new_movie.overview
    if new_movie.status:
        movie.status = new_movie.status
    if new_movie.budget:
        movie.budget = new_movie.budget
    if new_movie.revenue:
        movie.revenue = new_movie.revenue

    db.commit()
    db.refresh(movie)
    return {"detail": "Movie updated successfully."}
