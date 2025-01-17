import math

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

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
    MovieUpdateSchema
)


router = APIRouter()


@router.get("/movies/")
def get_movies(
        page: int =Query(ge=1, default=1),
        per_page: int = Query(ge=1, le=20, default=10),
        db: Session = Depends(get_db)
):
    total_items = db.query(MovieModel).count()
    total_pages = math.ceil(total_items / per_page)

    first_element = (page - 1) * per_page

    movies = db.query(MovieModel).offset(first_element).limit(per_page).all()

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


@router.post("/movies/", response_model=MovieCreateSchema, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreateSchema, db: Session = Depends(get_db)):

    exciting_movie = db.query(MovieModel).filter(
        MovieModel.name == movie.name,
        MovieModel.date == movie.date
    ).first()
    if exciting_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"A movie with the name '{movie.name}' and"
                           f" release date '{movie.date}' already exists."
            }
        )

    country = db.query(CountryModel).filter(
        CountryModel.code == movie.country
    ).first()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        db.commit()
        db.refresh(country)

    not_created_genres = []
    created_genres = []
    for genre_name in movie.genres:
        genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
        if not genre:
            genre = GenreModel(
                name=genre_name
            )
            not_created_genres.append(genre)
        else:
            created_genres.append(genre)
    db.bulk_save_objects(not_created_genres)
    db.commit()
    all_genres = not_created_genres + created_genres

    not_created_actors = []
    created_actors = []
    for actor_name in movie.actors:
        actor = db.query(ActorModel).filter(ActorModel.name == actor_name).first()
        if not actor:
            actor = ActorModel(
                name = actor_name
            )
            not_created_actors.append(actor)
        else:
            created_actors.append(actor)
    db.bulk_save_objects(not_created_actors)
    db.commit()
    all_actors = not_created_actors + created_actors

    not_created_languages = []
    created_languages = []
    for language_name in movie.languages:
        language = db.query(LanguageModel).filter(LanguageModel.name == language_name).first()
        if not language:
            language = LanguageModel(
                name=language_name
            )
            not_created_languages.append(language)
        else:
            created_languages.append(language)
    db.bulk_save_objects(not_created_languages)
    db.commit()
    all_languages = not_created_languages + created_languages

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
    db.commit()
    db.refresh(new_movie)

    new_movie.genres.extend(all_genres)
    new_movie.actors.extend(all_actors)
    new_movie.languages.extend(all_languages)
    db.commit

    return {
        "id": new_movie.id,
        "name": new_movie.name,
        "date": new_movie.date,
        "score": new_movie.score,
        "overview": new_movie.overview,
        "status": new_movie.status,
        "budget": new_movie.budget,
        "revenue": new_movie.revenue,
        "country": {
            "id": new_movie.country.id,
            "code": new_movie.country.code,
            "name": new_movie.country.name
        },
        "genres": [{"id": genre.id, "name": genre.name} for genre in all_genres],
        "actors": [{"id": actor.id, "name": actor.name} for actor in all_actors],
        "languages": [{"id": language.id, "name": language.name} for language in all_languages],
    }
