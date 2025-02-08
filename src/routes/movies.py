from math import ceil
from typing import Dict, Union, List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status
from pydantic_core.core_schema import AnySchema
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import update

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailsResponseSchema,
    MovieAddSchema,
    MovieUpdateSchema,
    MovieUpdateResponseSchema
)


router = APIRouter()


@router.get(
    "/movies/",
    response_model=Dict[str, Union[List[MovieListResponseSchema], Optional[str], int]]
)
def movies(
        db: Session = Depends(get_db),
        page: Annotated[int, Query(..., title="The page number to fetch", ge=1)] = 1,
        per_page: Annotated[int, Query(
            ..., title="Number of movies to fetch per page", ge=1, le=20
        )] = 10
) -> Dict[str, Union[List[MovieListResponseSchema], Optional[str], int]]:

    data = db.query(MovieModel).order_by(MovieModel.id.desc()).all()

    total_pages = ceil(len(data) / per_page)

    start = (page - 1) * per_page
    end = start + per_page

    items = len(data)
    if not items or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    if end > items:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"
    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    response = {
        "movies": data[start:end],
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": items
    }

    return response


def add_related_entities(entities: List[str], model, db) -> List[AnySchema]:
    existing_entities = []
    for entity in entities:
        existing_entity = db.query(model).filter(model.name == entity).first()
        if not existing_entity:
            existing_entity = model(name=entity)
            db.add(existing_entity)
            db.commit()
            db.refresh(existing_entity)
        existing_entities.append(existing_entity)
    return existing_entities


@router.post(
    "/movies/",
    response_model=MovieDetailsResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def add_movie(movie: MovieAddSchema, db: Session = Depends(get_db)):
    required_fields = ["name", "date", "score", "overview", "status", "budget", "revenue", "country"]
    for field in required_fields:
        if not getattr(movie, field, None):
            raise HTTPException(status_code=400, detail="Invalid input data.")

    country = db.query(CountryModel).filter(CountryModel.code == movie.country).first()
    if not country:
        country = CountryModel(code=movie.country)

    existing_movie = db.query(MovieModel).filter(
        (MovieModel.name == movie.name) & (MovieModel.date == movie.date)
    ).first()
    if existing_movie:
        raise HTTPException(
            status_code=409, detail=f"A movie with the name '{movie.name}' "
                                    f"and release date '{movie.date}' already exists."
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
    )

    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)

    if movie.genres:
        db_movie.genres = add_related_entities(movie.genres, GenreModel, db)

    if movie.actors:
        db_movie.actors = add_related_entities(movie.actors, ActorModel, db)

    if movie.languages:
        db_movie.languages = add_related_entities(movie.languages, LanguageModel, db)

    db.commit()
    db.refresh(db_movie)

    return db_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailsResponseSchema)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()


@router.patch(
    "/movies/{movie_id}/",
    response_model=MovieUpdateResponseSchema,
    status_code=status.HTTP_200_OK,
)
def update_movie(movie_update: MovieUpdateSchema, movie_id: int, db: Session = Depends(get_db)):
    existing_movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not existing_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    new_attributes = movie_update.model_dump(exclude_unset=True)

    if 'date' not in new_attributes:
        new_attributes['date'] = existing_movie.date

    try:
        db.execute(
            update(MovieModel)
            .where(MovieModel.id == movie_id)
            .values(new_attributes)
        )

        db.commit()
        db.refresh(existing_movie)

    except ValueError:
        db.rollback()
        existing_movie.detail = "Invalid input data."
        raise HTTPException(status_code=400, detail="Invalid input data.")

    existing_movie.detail = "Movie updated successfully."
    return existing_movie
