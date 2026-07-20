import math

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel, get_db
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from schemas.movies import (
    DetailMessageSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


router = APIRouter(prefix="/movies")

MOVIE_NOT_FOUND_MESSAGE = (
    "Movie with the given ID was not found."
)
INVALID_INPUT_MESSAGE = "Invalid input data."


async def get_or_create_genre(
    db: AsyncSession,
    name: str,
) -> GenreModel:
    normalized_name = name.strip()

    result = await db.execute(
        select(GenreModel).where(
            GenreModel.name == normalized_name
        )
    )
    genre = result.scalar_one_or_none()

    if genre is None:
        genre = GenreModel(name=normalized_name)
        db.add(genre)

    return genre


async def get_or_create_actor(
    db: AsyncSession,
    name: str,
) -> ActorModel:
    normalized_name = name.strip()

    result = await db.execute(
        select(ActorModel).where(
            ActorModel.name == normalized_name
        )
    )
    actor = result.scalar_one_or_none()

    if actor is None:
        actor = ActorModel(name=normalized_name)
        db.add(actor)

    return actor


async def get_or_create_language(
    db: AsyncSession,
    name: str,
) -> LanguageModel:
    normalized_name = name.strip()

    result = await db.execute(
        select(LanguageModel).where(
            LanguageModel.name == normalized_name
        )
    )
    language = result.scalar_one_or_none()

    if language is None:
        language = LanguageModel(name=normalized_name)
        db.add(language)

    return language


@router.get(
    "/",
    response_model=MovieListResponseSchema,
)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count(MovieModel.id))
    )
    total_items = count_result.scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found.",
        )

    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    previous_page = None
    next_page = None

    if page > 1:
        previous_page = (
            f"/theater/movies/"
            f"?page={page - 1}&per_page={per_page}"
        )

    if page < total_pages:
        next_page = (
            f"/theater/movies/"
            f"?page={page + 1}&per_page={per_page}"
        )

    return {
        "movies": movies,
        "prev_page": previous_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    raw_data: dict,
    db: AsyncSession = Depends(get_db),
):
    try:
        movie_data = MovieCreateSchema.model_validate(
            raw_data
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_INPUT_MESSAGE,
        ) from error

    movie_name = movie_data.name.strip()

    duplicate_result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_name,
            MovieModel.date == movie_data.date,
        )
    )
    existing_movie = duplicate_result.scalar_one_or_none()

    if existing_movie is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_name}' "
                f"and release date "
                f"'{movie_data.date.isoformat()}' "
                f"already exists."
            ),
        )

    country_code = movie_data.country.strip().upper()

    country_result = await db.execute(
        select(CountryModel).where(
            CountryModel.code == country_code
        )
    )
    country = country_result.scalar_one_or_none()

    if country is None:
        country = CountryModel(
            code=country_code,
            name=None,
        )
        db.add(country)

    unique_genres = dict.fromkeys(movie_data.genres)
    unique_actors = dict.fromkeys(movie_data.actors)
    unique_languages = dict.fromkeys(
        movie_data.languages
    )

    genres = [
        await get_or_create_genre(db, genre_name)
        for genre_name in unique_genres
    ]

    actors = [
        await get_or_create_actor(db, actor_name)
        for actor_name in unique_actors
    ]

    languages = [
        await get_or_create_language(
            db,
            language_name,
        )
        for language_name in unique_languages
    ]

    movie = MovieModel(
        name=movie_name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview.strip(),
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_INPUT_MESSAGE,
        ) from error

    created_movie_result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    created_movie = (
        created_movie_result
        .unique()
        .scalar_one()
    )

    return created_movie


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    movie = result.unique().scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIE_NOT_FOUND_MESSAGE,
        )

    return movie


@router.delete(
    "/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIE_NOT_FOUND_MESSAGE,
        )

    await db.delete(movie)
    await db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.patch(
    "/{movie_id}/",
    response_model=DetailMessageSchema,
)
async def update_movie(
    movie_id: int,
    raw_data: dict,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MOVIE_NOT_FOUND_MESSAGE,
        )

    try:
        update_data = MovieUpdateSchema.model_validate(
            raw_data
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_INPUT_MESSAGE,
        ) from error

    fields_to_update = update_data.model_dump(
        exclude_unset=True
    )

    for field_name, value in fields_to_update.items():
        setattr(movie, field_name, value)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_INPUT_MESSAGE,
        ) from error

    return {
        "detail": "Movie updated successfully."
    }
