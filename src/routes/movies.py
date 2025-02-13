from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import (
    MovieBaseSchema,
    MovieListSchema,
    MovieRetrieveSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListSchema)
def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Movies per page"),
    db: Session = Depends(get_db),
):
    total_items = db.query(MovieModel).count()
    total_pages = total_items // per_page + 1
    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    first_movie_id = (page - 1) * per_page
    db_movies = (
        db.query(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(first_movie_id)
        .limit(per_page)
        .all()
    )
    if not db_movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MovieListSchema(
        movies=db_movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/movies/", response_model=MovieRetrieveSchema, status_code=201)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):
    try:
        country = get_or_create_country(db=db, country_code=movie.country)
        genres = get_or_create_genre(db=db, genres_name=movie.genres)
        actors = get_or_create_actors(db=db, actors_name=movie.actors)
        languages = get_or_create_languages(db=db, languages_name=movie.languages)

        db_movie = (
            db.query(MovieModel).filter_by(name=movie.name, date=movie.date).first()
        )
        if db_movie:
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{movie.name}' and "
                f"release date '{movie.date}' already exists.",
            )

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
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    else:
        db.add(db_movie)
        db.commit()
        db.refresh(db_movie)
        return db_movie


@router.get("/movies/{movie_id}/", response_model=MovieRetrieveSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    db.delete(movie)
    db.commit()
    return Response(status_code=204)


@router.patch("/movies/{movie_id}/")
def update_movie(
    movie_id: int, movie_data: MovieUpdateSchema, db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter_by(id=movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_data.dict(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(movie, field, value)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid input data.")
    else:
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return {"detail": "Movie updated successfully."}


def get_or_create_country(db: Session, country_code: str):
    country = db.query(CountryModel).filter_by(code=country_code).first()
    if not country:
        country = CountryModel(code=country_code)
        db.add(country)
        db.commit()
        db.refresh(country)
    return country


def get_or_create_genre(db: Session, genres_name: list):
    genres: list = []
    for genre_name in genres_name:
        genre = db.query(GenreModel).filter_by(name=genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.commit()
            db.refresh(genre)
        genres.append(genre)
    return genres


def get_or_create_actors(db: Session, actors_name: list):
    actors: list = []
    for actor_name in actors_name:
        actor = db.query(ActorModel).filter_by(name=actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.commit()
            db.refresh(actor)
        actors.append(actor)
    return actors


def get_or_create_languages(db: Session, languages_name: list):
    languages = []
    for language_name in languages_name:
        language = db.query(LanguageModel).filter_by(name=language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.commit()
            db.refresh(language)
        languages.append(language)
    return languages
