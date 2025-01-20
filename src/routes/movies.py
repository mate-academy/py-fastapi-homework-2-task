from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import date
from src.database import get_db
from src.database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from src.schemas import movies
from src.schemas.movies import PaginationResponse, MovieResponse, MovieListItemResponse, MovieDetailResponse, \
    CountryResponse
from pydantic import parse_obj_as

router = APIRouter()


@router.post("/theater/movies/", response_model=movies.MovieResponse, status_code=status.HTTP_201_CREATED)
def add_film(film: movies.MovieCreate, db: Session = Depends(get_db)):
    existing_movie = db.query(MovieModel).filter(MovieModel.name == film.name, MovieModel.date == film.date).first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{film.name}' "
                   f"and release date '{film.date}' already exists.")

    country = db.query(CountryModel).filter(CountryModel.code == "US").first()
    if not country:
        country = CountryModel(code="US", name="United States")
        db.add(country)
        db.commit()
    print(f"Country found/created: {country.name}")

    new_movie = MovieModel(
        name=film.name,
        date=film.date,
        score=film.score,
        overview=film.overview,
        status=film.status,
        budget=film.budget,
        revenue=film.revenue,
        country_id=country.id
    )

    for genre_name in film.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.commit()
            db.refresh(genre)
            print(f"Genre created: {genre.name}")
        new_movie.genres.append(genre)

    for actor_name in film.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.commit()
            db.refresh(actor)
            print(f"Actor created: {actor.name}")
        new_movie.actors.append(actor)

    for language_name in film.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.commit()
            db.refresh(language)
            print(f"Language created: {language.name}")
        new_movie.languages.append(language)

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    # new_movie_dict = new_movie.__dict__.copy()
    # new_movie_dict['date'] = new_movie_dict['date'].strftime('%Y-%m-%d')
    return movies.MovieResponse.from_orm(new_movie)


@router.get("/theater/movies/", response_model=PaginationResponse)
def list_films(
        page: int = Query(1, ge=1, le=1000, description="Page number, must be >= 1"),
        per_page: int = Query(10, ge=1, le=50, description="Items per page, must be >= 1"),
        db: Session = Depends(get_db)
):
    if page < 1 or per_page < 1:
        raise HTTPException(status_code=422, detail="Input should be greater than or equal to 1")

    skip = (page - 1) * per_page
    films = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(skip).limit(per_page).all()

    if not films:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None

    movie_responses = [
        MovieListItemResponse(
            id=movie.id,
            name=movie.name,
            date=movie.date.strftime('%Y-%m-%d'),
            score=movie.score,
            overview=movie.overview
        )
        for movie in films
    ]

    return PaginationResponse(
        movies=movie_responses,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get("/theater/movies/{film_id}", response_model=movies.MovieResponse)
def read_film(film_id: int, db: Session = Depends(get_db)):
    db_film = db.query(MovieModel).filter(MovieModel.id == film_id).first()
    if not db_film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieResponse(
        id=db_film.id,
        name=db_film.name,
        date=db_film.date.strftime('%Y-%m-%d'),
        score=db_film.score,
        overview=db_film.overview,
        status=db_film.status.value.lower(),
        budget=db_film.budget,
        revenue=db_film.revenue,
        country_id=db_film.country.id,
        genres=[genre.name for genre in db_film.genres],
        actors=[actor.name for actor in db_film.actors],
        languages=[language.name for language in db_film.languages]
    )


@router.put("/theater/movies/{film_id}", response_model=movies.MovieResponse)
def edit_film(film_id: int, film: movies.MovieUpdate, db: Session = Depends(get_db)):
    db_film = db.query(MovieModel).filter(MovieModel.id == film_id).first()
    if not db_film:
        raise HTTPException(status_code=404, detail="Film not found")

    if film.score is not None and not (0 <= film.score <= 100):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
    if film.budget is not None and film.budget < 0:
        raise HTTPException(status_code=400, detail="Budget cannot be negative")
    if film.revenue is not None and film.revenue < 0:
        raise HTTPException(status_code=400, detail="Revenue cannot be negative")

    if film.name:
        db_film.name = film.name
    if film.date:
        db_film.date = film.date
    if film.score is not None:
        db_film.score = film.score
    if film.overview:
        db_film.overview = film.overview
    if film.status:
        db_film.status = film.status.value.lower(),
    if film.budget is not None:
        db_film.budget = film.budget
    if film.revenue is not None:
        db_film.revenue = film.revenue

    db.commit()
    db.refresh(db_film)

    return db_film


@router.get("/theater/movies/{movie_id}/", response_model=MovieDetailResponse)
def get_movie_by_id(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    country_data = None
    if movie.country:
        country_data = CountryResponse(id=movie.country.id, name=movie.country.name, code=movie.country.code)

    return MovieDetailResponse(
        id=movie.id,
        name=movie.name,
        date=movie.date.isoformat(),
        score=movie.score,
        overview=movie.overview,
        status=movie.status.value,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country_data,
        genres=[genre.name for genre in movie.genres],
        actors=[actor.name for actor in movie.actors],
        languages=[language.name for language in movie.languages]
    )


@router.patch("/theater/movies/{film_id}", response_model=movies.MovieResponse)
def patch_film(film_id: int, film: movies.MovieUpdate, db: Session = Depends(get_db)):
    db_film = db.query(MovieModel).filter(MovieModel.id == film_id).first()
    if not db_film:
        raise HTTPException(status_code=404, detail="Movie not found")

    if film.name:
        db_film.name = film.name
    if film.score:
        db_film.score = film.score

    db.commit()
    db.refresh(db_film)

    return db_film


@router.delete("/theater/movies/{film_id}/", status_code=status.HTTP_204_NO_CONTENT)
def remove_film(film_id: int, db: Session = Depends(get_db)):
    db_film = db.query(MovieModel).filter(MovieModel.id == film_id).first()
    if not db_film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    db.delete(db_film)
    db.commit()
    return None
