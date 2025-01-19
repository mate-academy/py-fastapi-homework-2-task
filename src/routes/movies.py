from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
import datetime
from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import MovieListResponse, MovieDetail, MovieCreate, MovieUpdate

router = APIRouter()


@router.get("/movies", response_model=MovieListResponse)
def get_movies(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):

    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    print(f"print get_movies: {movies}")

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    next_page =f"/theater/movies/?page={page + 1}&per_page={per_page}"
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


@router.post("/movies", response_model=MovieDetail, status_code=201)
def create_movie(
        movie: MovieCreate,
        db: Session = Depends(get_db)
):
    db_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name
    ).filter(
        MovieModel.date == movie.date
    ).first()
    # db_movie = db.query(MovieModel).filter_by(name=movie.name, date=movie.date).first()

    if db_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{db_movie.name}' and release date '{db_movie.date}' already exists."
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
    print("Country print: ", country)

    if movie.languages:
        for language_name in movie.languages:
            language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                db.commit()
                db.refresh(language)
            languages.append(language)

    if movie.actors:
        for actor_name in movie.actors:
            actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                db.commit()
                db.refresh(actor)
            actors.append(actor)

    if movie.genres:
        for genre_name in movie.genres:
            genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                db.commit()
                db.refresh(genre)
            genres.append(genre)

    if country is None:
        country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
        if country is None:
            country = CountryModel(code=movie.country)
            db.add(country)
            db.commit()
            db.refresh(country)

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
    except:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    raise HTTPException(status_code=201, detail="Movie created successfully.")


@router.get("/movies/{movie_id}", response_model=MovieDetail)
def get_movie(
        movie_id: int,
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    print(f"print get_movie: {movie}")
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}", status_code=204)
def delete_movie(
        movie_id: int,
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    print(f"print delete_movie: {movie}")
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()

@router.patch("/movies/{movie_id}", status_code=200)
def edit_movie(movie_id: int, movie_data: MovieUpdate, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    print(f"print edit_movie: {movie} and {movie_id}")
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    try:
        movie_date = movie_data.dict(exclude_unset=True)
        for key, value in movie_date.items():
            setattr(movie, key, value)
        db.commit()
        db.refresh(movie)
    except:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    # raise HTTPException(status_code=200, detail="Movie updated successfully.")
    return {"detail": "Movie updated successfully."}