import math
from typing import Union
import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieListSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MovieDetailSchema,
)


router = APIRouter()


def handle_movie_dependencies(
        elements: list[str],
        model: Union[GenreModel, ActorModel, LanguageModel],
        db: Session = Depends(get_db)
):

    not_created_elements = []
    created_elements = []
    for element_name in elements:
        element = db.query(model).filter(model.name == element_name).first()
        if not element:
            element = model(
                name=element_name
            )
            not_created_elements.append(element)
        else:
            created_elements.append(element)

    return not_created_elements, created_elements


@router.get("/movies/")
def get_movies(
        page: int = Query(ge=1, default=1),
        per_page: int = Query(ge=1, le=20, default=10),
        db: Session = Depends(get_db)
):
    total_items = db.query(MovieModel).count()
    total_pages = math.ceil(total_items / per_page)

    first_element = (page - 1) * per_page

    movies = db.query(MovieModel).order_by(MovieModel.id.desc()).offset(first_element).limit(per_page).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": [MovieListSchema.model_validate(movie) for movie in movies],
        "prev_page": prev_page if page > 1 else None,
        "next_page": next_page if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):

    try:
        with db.begin():
            exciting_movie = db.query(MovieModel).filter(
                MovieModel.name == movie.name,
                MovieModel.date == movie.date
            ).first()
            if exciting_movie:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A movie with the name '{movie.name}' and "
                           f"release date '{movie.date}' already exists."
                )

            country = db.query(CountryModel).filter(
                CountryModel.code == movie.country
            ).first()
            if not country:
                country = CountryModel(code=movie.country, name=None)
                db.add(country)
                db.flush()

            not_created_genres, created_genres = handle_movie_dependencies(movie.genres, GenreModel, db)
            db.add_all(not_created_genres)
            all_genres = not_created_genres + created_genres
            db.flush()

            not_created_actors, created_actors = handle_movie_dependencies(movie.actors, ActorModel, db)
            db.add_all(not_created_actors)
            all_actors = not_created_actors + created_actors
            db.flush()

            not_created_languages, created_languages = handle_movie_dependencies(movie.languages, LanguageModel, db)
            db.add_all(not_created_languages)
            all_languages = not_created_languages + created_languages
            db.flush()

            new_movie = MovieModel(
                name=movie.name,
                date=movie.date,
                score=movie.score,
                overview=movie.overview,
                status=movie.status,
                budget=movie.budget,
                revenue=movie.revenue,
                country=country,
            )
            db.add(new_movie)
            db.flush()

            new_movie.genres.extend(all_genres)
            new_movie.actors.extend(all_actors)
            new_movie.languages.extend(all_languages)

            return new_movie

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
def get_movie_by_id(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    logging.info(movie_data)
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
