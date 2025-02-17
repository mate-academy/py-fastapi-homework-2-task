from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    CountryModel
)
from database.session_postgresql import get_postgresql_db

from schemas.movies import (
    MovieResponse,
    MovieCreateResponse,
    MovieCreateRequest,
    PaginatedMoviesResponse,
    MovieUpdateRequest
)

router = APIRouter()


@router.get("/movies/", response_model=PaginatedMoviesResponse)
async def get_movies(page: int = 1,
                     per_page: int = 10,
                     db: Session = Depends(get_postgresql_db)):
    if page < 1 or per_page < 1 or per_page > 20:
        raise HTTPException(status_code=400,
                            detail="Invalid pagination parameters")

    offset = (page - 1) * per_page
    movies = db.query(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages)
    ).offset(offset).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found")

    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    prev_page = (f"/movies/?page={page - 1}"
                 f"&per_page={per_page}") if page > 1 else None
    next_page = (f"/movies/?page={page + 1}"
                 f"&per_page={per_page}") if page < total_pages else None

    movie_responses = [MovieResponse.from_orm(movie) for movie in movies]

    return PaginatedMoviesResponse(
        movies=movie_responses,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieCreateResponse)
async def create_movie(movie: MovieCreateRequest,
                       db: Session = Depends(get_postgresql_db)):
    existing_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).first()

    if existing_movie:
        raise HTTPException(status_code=409,
                            detail=f"A movie with the name '{movie.name}' "
                                   f"and release date '{movie.date}' already "
                                   f"exists."
                            )

    country = db.query(CountryModel).filter(
        CountryModel.code == movie.country
    ).first()

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        db.commit()

    genres = []
    for genre_name in movie.genres:
        genre = db.query(GenreModel).filter(
            GenreModel.name == genre_name
        ).first()

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor = db.query(ActorModel).filter(
            ActorModel.name == actor_name
        ).first()

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language = db.query(LanguageModel).filter(
            LanguageModel.name == language_name
        ).first()

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
        languages.append(language)

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
        languages=languages
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return MovieCreateResponse(
        id=new_movie.id,
        name=new_movie.name,
        date=new_movie.date,
        score=new_movie.score,
        overview=new_movie.overview,
        status=new_movie.status,
        budget=new_movie.budget,
        revenue=new_movie.revenue,
        country={"id": country.id,
                 "code": country.code,
                 "name": country.name},
        genres=[{"id": genre.id, "name": genre.name} for genre in genres],
        actors=[{"id": actor.id, "name": actor.name} for actor in actors],
        languages=[{"id": language.id,
                    "name": language.name} for language in languages]
    )


@router.get("/movies/{movie_id}/", response_model=MovieCreateResponse)
async def get_movie_details(movie_id: int,
                            db: Session = Depends(get_postgresql_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    return MovieCreateResponse(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country={"id": movie.country.id,
                 "code": movie.country.code,
                 "name": movie.country.name},
        genres=[{"id": genre.id,
                 "name": genre.name} for genre in movie.genres],
        actors=[{"id": actor.id,
                 "name": actor.name} for actor in movie.actors],
        languages=[{"id": language.id,
                    "name": language.name} for language in movie.languages]
    )


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int,
                       db: Session = Depends(get_postgresql_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    db.delete(movie)
    db.commit()

    return {"detail": "Movie deleted successfully."}


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int,
                       movie_update: MovieUpdateRequest,
                       db: Session = Depends(get_postgresql_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Movie with the given ID was not found.")

    if movie_update.score is not None and (
            movie_update.score < 0 or movie_update.score > 100):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid input data for score.")

    if movie_update.budget is not None and movie_update.budget < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid input data for budget.")

    if movie_update.revenue is not None and movie_update.revenue < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid input data for revenue.")

    if movie_update.name is not None:
        movie.name = movie_update.name
    if movie_update.date is not None:
        try:
            movie.date = datetime.strptime(movie_update.date,
                                           "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use 'YYYY-MM-DD'."
            )
    if movie_update.score is not None:
        movie.score = movie_update.score
    if movie_update.overview is not None:
        movie.overview = movie_update.overview
    if movie_update.status is not None:
        movie.status = movie_update.status
    if movie_update.budget is not None:
        movie.budget = movie_update.budget
    if movie_update.revenue is not None:
        movie.revenue = movie_update.revenue

    db.commit()

    return {"detail": "Movie updated successfully."}
