import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Request
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from typing import Annotated, Optional
from src.database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from src.database import get_db
from src.schemas.movies import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateResponseSchema,
    MovieUpdateResponseSchema,
    MovieListItemResponseSchema
)

router = APIRouter()


@router.get("/movies/",)
def get_movies(
        request: Request,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
        db: Session = Depends(get_db),
):
    start = (page - 1) * per_page
    films = (db.query(MovieModel).order_by(MovieModel.id.desc()).offset(start).limit(per_page).all())
    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    if not films:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    return {
        "movies": [MovieListItemResponseSchema.model_validate(film) for film in films],
        "prev_page": prev_page if page > 1 else None,
        "next_page": next_page if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
def get_movie(
        request: Request,
        movie_id: int,
        db: Session = Depends(get_db),
) -> MovieDetailResponseSchema:
    film = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not film:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    return film


@router.post(
    "/movies/",
    response_model=MovieCreateResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def create_movie(
        movie_data: MovieCreateResponseSchema,
        db: Session = Depends(get_db)
):
    with db.begin():
        existing_movie = db.query(MovieModel).filter(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        ).first()
        if existing_movie:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A movie with the name '{movie_data.name}' "
                       f"and release date '{movie_data.date}' already exists."
            )

    country = db.query(CountryModel).filter(
        CountryModel.code == movie_data.country
    ).first()
    if not country:
        country = CountryModel(code=movie_data.country, name="Unknown Country")
        db.add(country)
        db.flush()

    if not movie_data.name or not movie_data.date or not movie_data.overview or not movie_data.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fields 'name', 'date', 'overview' and 'status' is requir to create movie."
        )

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id
    )

    genres_names = movie_data.genres
    if genres_names:
        genres = []
        for genre_name in genres_names:
            genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                db.commit()
                db.refresh(genre)
            genres.append(genre)
        new_movie.genres = genres

    actors_names = movie_data.actors
    if actors_names:
        actors = []
        for actor_name in actors_names:
            actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                db.commit()
                db.refresh(actor)
            actors.append(actor)
        new_movie.actors = actors

    languages_names = movie_data.languages
    if languages_names:
        languages = []
        for language_name in languages_names:
            language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                db.commit()
                db.refresh(language)
            languages.append(language)
        new_movie.languages = languages

    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    return MovieCreateResponseSchema(
        id=new_movie.id,
        name=new_movie.name,
        date=new_movie.date,
        score=new_movie.score,
        overview=new_movie.overview,
        status=new_movie.status,
        budget=new_movie.budget,
        revenue=new_movie.revenue,
        country=country.code,
        genres=[genre.name for genre in new_movie.genres],
        actors=[actor.name for actor in new_movie.actors],
        languages=[language.name for language in new_movie.languages],
    )


@router.patch("/movies/{movie_id}/", response_model=MovieUpdateResponseSchema)
def update_movie(
        movie_id: int,
        movie_data: MovieUpdateResponseSchema,
        db: Session = Depends(get_db),
):
    movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
        request: Request,
        movie_id: int,
        db: Session = Depends(get_db),
) -> None:
    film = db.query(MovieModel).filter(MovieModel.id == movie_id).first()
    if not film:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    db.delete(film)
    db.commit()
    return None
