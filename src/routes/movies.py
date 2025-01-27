from fastapi import APIRouter, Depends, HTTPException, Query
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
    PaginatedMovieResponseSchema,
    CreateMovieSchema,
    CreateResponseMovieSchema,
    MovieDetailSchema,
    UpdateMovieRequest
)
from services.crud import (
    delete_movie,
    get_movies,
    create_movie,
    get_movie_by_id,
    update_movie,
)

router = APIRouter()


@router.get(
    "/movies/",
    response_model=PaginatedMovieResponseSchema,
    status_code=status.HTTP_200_OK
)
def read_movies(
        db: Session = Depends(get_db),
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10
):
    total_items = db.query(MovieModel).count()
    total_pages = (total_items + per_page - 1) // per_page

    offset = (page - 1) * per_page
    limit = per_page

    movies = get_movies(db, offset, limit)

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return PaginatedMovieResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post(
    "/movies/",
    response_model=CreateResponseMovieSchema,
    status_code=status.HTTP_201_CREATED
)
def add_movie(
        movie: CreateMovieSchema,
        db: Session = Depends(get_db)
):
    movie_exists = db.query(MovieModel).filter_by(name=movie.name, date=movie.date).first()

    if movie_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    try:
        new_movie = create_movie(movie, db)
        return CreateResponseMovieSchema.model_validate(new_movie)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    return get_movie_by_id(db, movie_id)


@router.delete("/movies/{movie_id}/", status_code=204)
def delete_movie_by_id(movie_id: int, db: Session = Depends(get_db)):
    delete_movie(db, movie_id)
    return {}


@router.patch("/movies/{movie_id}/")
def update_movie_by_id(movie_id: int, updated_data: UpdateMovieRequest, db: Session = Depends(get_db)):
    update_data_dict = updated_data.model_dump(exclude_unset=True)
    update_movie(db, movie_id, update_data_dict)
    return {"detail": "Movie updated successfully."}
