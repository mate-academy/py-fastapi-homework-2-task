
import math

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import (
    ActorModel,
    CountryModel,
    GenreModel,
    LanguageModel,
)
from schemas import MovieDetailSchema
from schemas.movies import (
    MovieCreateSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)

router = APIRouter()


async def _get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .execution_options(populate_existing=True)
    )


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    total_items = await db.scalar(
        select(func.count(MovieModel.id))
    )

    total_pages = math.ceil(total_items / per_page)

    movies = (
        await db.scalars(
            select(MovieModel)
            .order_by(MovieModel.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
    ).all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found.",
        )

    return {
        "movies": movies,
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie.name}' "
                f"and release date '{movie.date}' already exists."
            ),
        )

    country = await db.scalar(
        select(CountryModel).where(
            CountryModel.code == movie.country
        )
    )

    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)

    genres = []

    for genre_name in movie.genres:
        genre = await db.scalar(
            select(GenreModel).where(
                GenreModel.name == genre_name
            )
        )

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)

        genres.append(genre)

    actors = []

    for actor_name in movie.actors:
        actor = await db.scalar(
            select(ActorModel).where(
                ActorModel.name == actor_name
            )
        )

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)

        actors.append(actor)

    languages = []

    for language_name in movie.languages:
        language = await db.scalar(
            select(LanguageModel).where(
                LanguageModel.name == language_name
            )
        )

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)

        languages.append(language)

    db_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    try:
        db.add(db_movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    return await _get_movie(db_movie.id, db)


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await _get_movie(movie_id, db)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.id == movie_id
        )
    )

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int,
    movie: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    db_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.id == movie_id
        )
    )

    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    return {"detail": "Movie updated successfully."}
