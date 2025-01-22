from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import (MovieModel,
                             CountryModel,
                             GenreModel,
                             ActorModel,
                             LanguageModel)
from schemas.movies import (MoviesBase,
                            MovieBase,
                            MovieDetailSchema,
                            MovieCreateSchema,
                            CountryBase,
                            GenreBase,
                            ActorBase,
                            LanguageBase,
                            MovieUpdateSchema)

router = APIRouter()


# get all movies
@router.get("/movies/", response_model=MoviesBase)
def get_movies(db: Session = Depends(get_db),
               page: int = Query(1, ge=1),
               per_page: int = Query(10, ge=1)) -> MoviesBase:
    movies = db.query(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).order_by(desc(MovieModel.id)).limit(per_page).offset((page - 1) * per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if len(movies) == per_page else None
    total_pages = (db.query(MovieModel).count() + per_page - 1) // per_page
    total_items = db.query(MovieModel).count()

    return MoviesBase(
        movies=[
            MovieBase(
                id=movie.id,
                name=movie.name,
                date=movie.date,
                score=movie.score,
                overview=movie.overview
            ) for movie in movies
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_items=total_items,
        total_pages=total_pages
    )


# movie creation
@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)) -> MovieDetailSchema:
    movie_found = db.query(MovieModel).filter(MovieModel.name == movie.name, MovieModel.date == movie.date).first()

    if movie_found:
        raise HTTPException(status_code=409, detail=f"A movie with the name"
                                                    f" '{movie.name}' and"
                                                    f" release date '{movie.date}' already exists.")

    country = db.query(CountryModel).filter(CountryModel.name == movie.country).first()

    if not country:
        country = CountryModel(name=movie.country, code=f"{movie.country}")
        db.add(country)
        db.commit()
        db.refresh(country)

    genres = []
    for genre in movie.genres:
        genre_found = db.query(GenreModel).filter(GenreModel.name == genre).first()
        if not genre_found:
            genre_found = GenreModel(name=genre)
            db.add(genre_found)
            db.commit()
            db.refresh(genre_found)
        genres.append(genre_found)

    actors = []
    for actor in movie.actors:
        actor_found = db.query(ActorModel).filter(ActorModel.name == actor).first()
        if not actor_found:
            actor_found = ActorModel(name=actor)
            db.add(actor_found)
            db.commit()
            db.refresh(actor_found)
        actors.append(actor_found)

    languages = []
    for language in movie.languages:
        language_found = db.query(LanguageModel).filter(LanguageModel.name == language).first()
        if not language_found:
            language_found = LanguageModel(name=language)
            db.add(language_found)
            db.commit()
            db.refresh(language_found)
        languages.append(language_found)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
        budget=movie.budget,
        revenue=movie.revenue
    )

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return MovieDetailSchema(
        id=new_movie.id,
        name=new_movie.name,
        date=new_movie.date,
        score=new_movie.score,
        overview=new_movie.overview,
        status=new_movie.status,
        countries=[CountryBase(id=country.id, name=country.name, code=country.code)],
        genres=[GenreBase(id=genre.id, name=genre.name) for genre in new_movie.genres],
        actors=[ActorBase(id=actor.id, name=actor.name) for actor in new_movie.actors],
        languages=[LanguageBase(id=language.id, name=language.name) for language in new_movie.languages],
        budget=new_movie.budget,
        revenue=new_movie.revenue
    )


# get movie by id
@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetailSchema:
    movie = db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    country = movie.country
    if not country or not country.name:
        raise HTTPException(status_code=404, detail="Country information is invalid.")

    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        countries=[CountryBase(id=country.id, code=country.code, name=country.name)],
        genres=[GenreBase(id=genre.id, name=genre.name) for genre in movie.genres],
        actors=[ActorBase(id=actor.id, name=actor.name) for actor in movie.actors],
        languages=[LanguageBase(id=language.id, name=language.name) for language in movie.languages],
    )


# delete movie
@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(movie)
    db.commit()


# update movie
@router.put("/movies/{movie_id}/", response_model=MovieDetailSchema)
def update_movie(movie_id: int, movie: MovieUpdateSchema, db: Session = Depends(get_db)) -> MovieDetailSchema:
    existing_movie = db.get(MovieModel, movie_id)

    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie.name is not None:
        existing_movie.name = movie.name
    if movie.date is not None:
        existing_movie.date = movie.date
    if movie.score is not None:
        existing_movie.score = movie.score
    if movie.overview is not None:
        existing_movie.overview = movie.overview
    if movie.status is not None:
        existing_movie.status = movie.status
    if movie.budget is not None:
        existing_movie.budget = movie.budget
    if movie.revenue is not None:
        existing_movie.revenue = movie.revenue

    if movie.country is not None:
        country = db.query(CountryModel).filter(CountryModel.name == movie.country).first()
        if not country:
            country = CountryModel(name=movie.country)
            db.add(country)
            db.commit()
            db.refresh(country)
        existing_movie.country_id = country.id

    if movie.genres is not None:
        genres = []
        for genre in movie.genres:
            genre_found = db.query(GenreModel).filter(GenreModel.name == genre).first()
            if not genre_found:
                genre_found = GenreModel(name=genre)
                db.add(genre_found)
                db.commit()
                db.refresh(genre_found)
            genres.append(genre_found)
        existing_movie.genres = genres

    if movie.actors is not None:
        actors = []
        for actor in movie.actors:
            actor_found = db.query(ActorModel).filter(ActorModel.name == actor).first()
            if not actor_found:
                actor_found = ActorModel(name=actor)
                db.add(actor_found)
                db.commit()
                db.refresh(actor_found)
            actors.append(actor_found)
        existing_movie.actors = actors

    if movie.languages is not None:
        languages = []
        for language in movie.languages:
            language_found = db.query(LanguageModel).filter(LanguageModel.name == language).first()
            if not language_found:
                language_found = LanguageModel(name=language)
                db.add(language_found)
                db.commit()
                db.refresh(language_found)
            languages.append(language_found)
        existing_movie.languages = languages

    try:
        db.commit()
        db.refresh(existing_movie)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error occurred while updating the movie.")

    return MovieDetailSchema(
        id=existing_movie.id,
        name=existing_movie.name,
        date=existing_movie.date,
        score=existing_movie.score,
        overview=existing_movie.overview,
        status=existing_movie.status,
        budget=existing_movie.budget,
        revenue=existing_movie.revenue,
        countries=[CountryBase(id=existing_movie.country.id,
                               code=existing_movie.country.code,
                               name=existing_movie.country.name)],
        genres=[GenreBase(id=genre.id, name=genre.name) for genre in existing_movie.genres],
        actors=[ActorBase(id=actor.id, name=actor.name) for actor in existing_movie.actors],
        languages=[LanguageBase(id=language.id, name=language.name) for language in existing_movie.languages],
    )
