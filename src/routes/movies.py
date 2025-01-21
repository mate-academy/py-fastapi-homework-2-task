import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
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
    MoviesSchema,
    MovieSchema,
    MovieDetailSchema,
    GenreSchema,
    ActorSchema,
    LanguageSchema,
    CountrySchema,
    MovieCreateSchema,
    MovieUpdateSchema
)

router = APIRouter()


@router.get("/movies/")
def read_movies(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
) -> MoviesSchema:
    total_items = db.query(MovieModel).count()
    total_pages = math.ceil(total_items / per_page)
    if not total_items or page > total_pages:
        raise HTTPException(404, "No movies found.")
    count = (page - 1) * per_page
    movies = (
        db
        .query(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(count)
        .limit(per_page)
        .all()
    )

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MoviesSchema(
        movies=[
            MovieSchema(
                id=movie.id,
                name=movie.name,
                date=movie.date,
                score=movie.score,
                overview=movie.overview,
            )
            for movie in movies
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201
)
def create_movie(
        movie: MovieCreateSchema,
        db: Session = Depends(get_db),
) -> MovieDetailSchema:
    find_movie = (
        db
        .query(MovieModel)
        .filter(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
        .first()
    )
    if find_movie:
        raise HTTPException(
            409,
            f"A movie with the name '{movie.name}' "
            f"and release date '{movie.date}' already exists."
        )
    movie_genres = []
    for genre in movie.genres:
        movie_genre = (
            db
            .query(GenreModel)
            .filter(GenreModel.name == genre)
            .first()
        )

        if not movie_genre:
            db.add(
                GenreModel(name=genre)
            )
            db.commit()
            movie_genre = (
                db
                .query(GenreModel)
                .filter(GenreModel.name == genre)
                .first()
            )
        movie_genres.append(movie_genre)

    movie_actors = []
    for actor in movie.actors:
        movie_actor = (
            db
            .query(ActorModel)
            .filter(ActorModel.name == actor)
            .first()
        )

        if not movie_actor:
            db.add(
                ActorModel(name=actor)
            )
            db.commit()
            movie_actor = (
                db
                .query(ActorModel)
                .filter(ActorModel.name == actor)
                .first()
            )
        movie_actors.append(movie_actor)

    movie_languages = []
    for language in movie.languages:
        movie_language = (
            db
            .query(LanguageModel)
            .filter(LanguageModel.name == language)
            .first()
        )

        if not movie_language:
            db.add(
                LanguageModel(name=language)
            )
            db.commit()
            movie_language = (
                db
                .query(LanguageModel)
                .filter(LanguageModel.name == language)
                .first()
            )
        movie_languages.append(movie_language)

    movie_country = (
        db
        .query(CountryModel)
        .filter(CountryModel.code == movie.country)
        .first()
    )
    if not movie_country:
        db.add(
            CountryModel(code=movie.country)
        )
        db.commit()
        movie_country = (
            db
            .query(CountryModel)
            .filter(CountryModel.code == movie.country)
            .first()
        )

    db.add(
        MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=movie_country,
            genres=movie_genres,
            actors=movie_actors,
            languages=movie_languages,
        )
    )
    db.commit()
    new_movie = db.query(MovieModel).filter(MovieModel.name == movie.name).first()

    return MovieDetailSchema(
        id=new_movie.id,
        name=new_movie.name,
        date=new_movie.date,
        score=new_movie.score,
        overview=new_movie.overview,
        status=new_movie.status,
        country=CountrySchema(
            id=movie_country.id,
            code=movie_country.code,
            name=movie_country.name
        ),
        genres=[
            GenreSchema(
                id=genre.id,
                name=genre.name
            )for genre in movie_genres
        ],
        actors=[
            ActorSchema(
                id=actor.id,
                name=actor.name
            )for actor in movie_actors
        ],
        languages=[
            LanguageSchema(
                id=language.id,
                name=language.name
            )
            for language in movie_languages
        ],
        budget=new_movie.budget,
        revenue=new_movie.revenue,
    )


@router.get("/movies/{movie_id}/")
def read_movie(
        movie_id: int,
        db: Session = Depends(get_db)
) -> MovieDetailSchema:
    movie = db.query(MovieModel).get(movie_id)
    if not movie:
        raise HTTPException(404, "Movie with the given ID was not found.")

    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=CountrySchema(
            id=movie.country.id,
            code=movie.country.code,
            name=movie.country.name
        ),
        genres=[
            GenreSchema(
                id=genre.id,
                name=genre.name
            ) for genre in movie.genres
        ],
        actors=[
            ActorSchema(
                id=actor.id,
                name=actor.name
            ) for actor in movie.actors
        ],
        languages=[
            LanguageSchema(
                id=language.id,
                name=language.name
            )
            for language in movie.languages
        ],
    )


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie(
        movie_id: int,
        db: Session = Depends(get_db)
):
    movie = db.query(MovieModel).get(movie_id)
    if not movie:
        raise HTTPException(404, "Movie with the given ID was not found.")
    db.delete(movie)
    db.commit()
    return {
        "msg": "Movie has been deleted."
    }


@router.patch(
    "/movies/{movie_id}/",
)
def update_movie( # noqa
        movie_id: int,
        movie: MovieUpdateSchema,
        db: Session = Depends(get_db)
):
    need_movie = db.query(MovieModel).get(movie_id)
    if not need_movie:
        raise HTTPException(404, "Movie with the given ID was not found.")

    if movie.name:
        need_movie.name = movie.name

    if movie.date:
        need_movie.date = movie.date

    if movie.overview:
        need_movie.overview = movie.overview

    if movie.status:
        need_movie.status = movie.status

    if movie.country:
        country = (
            db
            .query(CountryModel)
            .filter(CountryModel.code == movie.country)
            .first()
        )
        if not country:
            db.add(CountryModel(code=movie.country))
            country = (
                db
                .query(CountryModel)
                .filter(CountryModel.code == movie.country)
                .first()
            )
        need_movie.country = country

    if movie.genres:
        genres = []
        for genre in movie.genres:
            movie_genre = (
                db
                .query(GenreModel)
                .filter(GenreModel.name == genre)
                .first()
            )
            if not movie_genre:
                db.add(GenreModel(name=genre))
                db.commit()
                movie_genre = (
                    db
                    .query(GenreModel)
                    .filter(GenreModel.name == genre)
                    .first()
                )
            genres.append(movie_genre)
        need_movie.genres = genres

    if movie.actors:
        actors = []
        for actor in movie.actors:
            movie_actor = (
                db
                .query(ActorModel)
                .filter(ActorModel.name == actor)
                .first()
            )
            if not movie_actor:
                db.add(ActorModel(name=actor))
                db.commit()
                movie_actor = (
                    db
                    .query(ActorModel)
                    .filter(ActorModel.name == actor)
                    .first()
                )
            actors.append(movie_actor)
        need_movie.actors = actors

    if movie.languages:
        languages = []
        for language in movie.language:
            movie_language = (
                db
                .query(LanguageModel)
                .filter(LanguageModel.name == language)
                .first()
            )
            if not movie_language:
                db.add(ActorModel(name=language))
                db.commit()
                movie_language = (
                    db
                    .query(LanguageModel)
                    .filter(LanguageModel.name == language)
                    .first()
                )
            languages.append(movie_language)
        need_movie.languages = languages

    if movie.score:
        need_movie.score = movie.score

    if movie.budget:
        need_movie.budget = movie.budget

    if movie.revenue:
        need_movie.revenue = movie.revenue
    db.commit()
    return {
        "detail": "Movie updated successfully."
    }
