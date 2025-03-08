from http.client import HTTPResponse

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Response
from pytz import country_names
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
from schemas.movies import MovieListSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListSchema)
def get_movies(page: int = 1, per_page: int = 10, db: Session = Depends(get_db)):
    if page < 1:
        raise HTTPException(
            status_code=422,
            detail="ensure this value is greater than or equal to 1"
        )
    if not 1 <= per_page <= 20:
        raise HTTPException(
            status_code=422,
            detail="ensure this value is greater than or equal to 1 and smaller than 21"
        )
    start_id = (page * per_page) - per_page
    end_id = page * per_page
    query_set = db.query(MovieModel).all()
    movies = [movie for movie in query_set if start_id < movie.id <= end_id]
    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )
    total_pages = len(query_set) // per_page if len(query_set) % per_page == 0 else (len(query_set) // per_page) + 1
    base_page_url = "/api/v1/theater/movies/"
    response_for = {
        "movies": movies,
        "total_items": f"{len(query_set)}",
        "total_pages": total_pages,

    }
    if total_pages > page:
        response_for["next_page"] = f"{base_page_url}?page={page + 1}&per_page={per_page}"
    if page > 1:
        response_for["prev_page"] = f"{base_page_url}?page={page - 1}&per_page={per_page}"
    return response_for

@router.get("/movies/{movie_id}", response_model=MovieDetailSchema)
def get_movie_detail_page(movie_id: int, db: Session = Depends(get_db)):
    result = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Movie with provide id not found!")
    return result


@router.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="The movie with the specified ID does not exist.")
    db.delete(movie)
    db.commit()
    return Response(status_code=204, content="The movie was successfully deleted")


@router.post("/movies/", response_model=MovieDetailSchema)
def create_new_movie(movie_data: MovieCreateSchema, db: Session = Depends(get_db)):
    if not 0 <= movie_data.score <= 100:
        raise HTTPException(status_code=400, detail="Bad request")
    if movie_data.budget < 0 or movie_data.revenue < 0:
        raise HTTPException(status_code=400, detail="Bad request")
    country = db.query(CountryModel).filter(CountryModel.code == movie_data.country).first()
    if not country:
        raise HTTPException(status_code=404, detail="country not found")

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        status=movie_data.status,
        overview=movie_data.overview,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=[],
        actors=[],
        languages=[]
    )

    for genre_name in movie_data.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            db.flush()
        new_movie.genres.append(genre)

    for actor_name in movie_data.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            db.flush()
        new_movie.actors.append(actor)

    for language_name in movie_data.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name)
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            db.flush()
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@router.patch("/movies/{movie_id}", response_model=MovieDetailSchema)
def update_movie(update_data: MovieUpdateSchema, movie_id: int, db: Session = Depends(get_db)):
    old_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    data_check = update_data.dict(exclude_unset=True)
    if data_check["score"] and not 0 <= data_check["score"] <= 100:
        raise HTTPException(status_code=400, detail="Bad request.")
    if data_check["budget"] and data_check["budget"] < 0:
        raise HTTPException(status_code=400, detail="Bad request.")
    if data_check["revenue"] and data_check["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Bad request.")
    if not old_movie:
        raise HTTPException(status_code=404, detail="Movie not found.")
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(old_movie, key, value)
    db.commit()
    db.refresh(old_movie)
    return old_movie
