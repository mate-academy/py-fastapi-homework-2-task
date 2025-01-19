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

# from src.crud import create_country_by_code, create_instance_by_name, check_or_create_many_instances_by_name

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponse)
def get_movies(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
) -> MovieListResponse:

    movies = (
        db.query(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    print(f"print get_movies: {movies}")

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
    db_movie = (
        db.query(MovieModel)
        .filter(MovieModel.name == movie.name)
        .filter(MovieModel.date == movie.date)
        .first()
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
        # languages.extend(check_or_create_many_instances_by_name(movie.languages, LanguageModel, db))
        for language_name in movie.languages:
            language = (
                db.query(LanguageModel)
                .filter(LanguageModel.name == language_name)
                .first()
            )
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                db.commit()
                db.refresh(language)
            languages.append(language)

    if movie.actors:
        # actors.extend(check_or_create_many_instances_by_name(movie.actors, ActorModel, db))
        for actor_name in movie.actors:
            actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
            if not actor:
                # create_instance_by_name(name=actor_name, model=ActorModel)
                actor = ActorModel(name=actor_name)
                db.add(actor)
                db.commit()
                db.refresh(actor)
            actors.append(actor)

    if movie.genres:
        # genres.extend(check_or_create_many_instances_by_name(movie.genres, GenreModel, db))
        for genre_name in movie.genres:
            genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                db.commit()
                db.refresh(genre)
            genres.append(genre)

    if not country:
        # country = create_country_by_code(code=movie.country, db=db)
        country = CountryModel(code=movie.country)
        db.add(country)
        db.commit()
        db.refresh(country)

    print(f"Genres: {genres}")
    print(f"Actors: {actors}")
    print(f"Languages: {languages}")
    print(f"Country: {country}")
    print(f"Movie: {movie.model_dump()}")
    try:
        new_movie = MovieModel(
            **movie.model_dump(exclude={"country", "genres", "actors", "languages"}),
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        db.add(new_movie)
        db.commit()
        db.refresh(new_movie)
        return new_movie
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    # raise HTTPException(status_code=201, detail="Movie created successfully.")


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetail:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    print(f"print get_movie: {movie}")
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)) -> None:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    print(f"print delete_movie: {movie}")
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    db.delete(movie)
    db.commit()


@router.patch("/movies/{movie_id}/", status_code=200)
def edit_movie(movie_id: int, movie_data: MovieUpdate, db: Session = Depends(get_db)) -> dict[str, str]:
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    print(f"print edit_movie: {movie} and {movie_id}")
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
    # raise HTTPException(status_code=200, detail="Movie updated successfully.")
    return {"detail": "Movie updated successfully."}

    # db_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    # if not db_movie:
    #     raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    #
    # if movie.name:
    #     if len(movie.name) > 255:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Invalid input data."
    #         )
    #     db_movie.name = movie.name
    #
    # if movie.date:
    #     if movie.date > datetime.datetime.now().date() + datetime.timedelta(days=365):
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Invalid input data."
    #         )
    #     db_movie.date = movie.date
    #
    # if movie.score:
    #     if not (0 <= movie.score <= 100):
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Invalid input data."
    #         )
    #     db_movie.score = movie.score
    #
    # if movie.overview:
    #     db_movie.overview = movie.overview
    # if movie.status:
    #     db_movie.status = movie.status
    #
    # if movie.budget:
    #     if movie.budget < 0:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Invalid input data."
    #         )
    #     db_movie.budget = movie.budget
    #
    # if movie.revenue:
    #     if movie.revenue < 0:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Invalid input data."
    #         )
    #     db_movie.revenue = movie.revenue
    #
    # db.commit()
    # db.refresh(db_movie)
    # return {"detail": "Movie updated successfully.", "movie": db_movie}
