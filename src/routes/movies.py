import math
from typing import Annotated
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)
from services.crud import (
    count_movies,
    create_movie_record,
    delete_movie_record,
    fetch_movies_page,
    get_movie_record_by_id,
    get_or_create_entity,
    get_or_create_named_entities,
    movie_exists,
    update_movie_record,
)


router = APIRouter()


@router.get(
    "/movies/",
    name="movie-list",
    response_model=MovieListResponseSchema,
)
async def get_all_movies(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    movies = await fetch_movies_page(
        db=db,
        page=page,
        per_page=per_page,
    )

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_items = await count_movies(db)
    total_pages = math.ceil(total_items / per_page)

    router_path = router.url_path_for("movie-list")
    base_path = f"/theater{router_path}"

    prev_page = None
    if page > 1:
        query_params = urlencode(
            {
                "page": page - 1,
                "per_page": per_page,
            }
        )
        prev_page = f"{base_path}?{query_params}"

    next_page = None
    if page < total_pages:
        query_params = urlencode(
            {
                "page": page + 1,
                "per_page": per_page,
            }
        )
        next_page = f"{base_path}?{query_params}"

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    name="movie-create",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    duplicate_message = (
        f"A movie with the name '{movie.name}' "
        f"and release date '{movie.date}' already exists."
    )

    already_exists = await movie_exists(
        db=db,
        movie_name=movie.name,
        movie_date=movie.date,
    )

    if already_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=duplicate_message,
        )

    try:
        actors = await get_or_create_named_entities(
            db=db,
            model=ActorModel,
            names=movie.actors,
        )

        genres = await get_or_create_named_entities(
            db=db,
            model=GenreModel,
            names=movie.genres,
        )

        languages = await get_or_create_named_entities(
            db=db,
            model=LanguageModel,
            names=movie.languages,
        )

        country, _ = await get_or_create_entity(
            db=db,
            model=CountryModel,
            code=movie.country.strip().upper(),
        )

        movie_data = movie.model_dump(
            exclude={
                "actors",
                "genres",
                "languages",
                "country",
            }
        )

        new_movie = await create_movie_record(
            db=db,
            movie_data=movie_data,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )

        loaded_movie = await get_movie_record_by_id(
            db=db,
            movie_id=new_movie.id,
        )

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=duplicate_message,
        ) from error

    if loaded_movie is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load the created movie.",
        )

    return MovieDetailSchema.model_validate(loaded_movie)


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    movie = await get_movie_record_by_id(
        db=db,
        movie_id=movie_id,
    )

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    deleted_movie = await delete_movie_record(
        db=db,
        movie_id=movie_id,
    )

    if deleted_movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        updated_movie = await update_movie_record(
            db=db,
            movie_id=movie_id,
            movie_data=movie,
        )

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from error

    if updated_movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return {"detail": "Movie updated successfully."}
