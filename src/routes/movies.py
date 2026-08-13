from math import ceil
from datetime import date, timedelta
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreate,
    MovieDetailSchema, MovieUpdate
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20)
):
    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    if total_items == 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found.",
        )

    total_pages = ceil(total_items / per_page)

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_db),
):
    # Проверка даты
    if movie.date > date.today() + timedelta(days=365):
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    # Проверка на дубликат
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie.name}' "
                f"and release date '{movie.date}' already exists."
            ),
        )

    # ---------- COUNTRY ----------
    country = await db.scalar(
        select(CountryModel).where(
            CountryModel.code == movie.country
        )
    )

    if country is None:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    # ---------- GENRES ----------
    genres = []

    for genre_name in movie.genres:
        genre = await db.scalar(
            select(GenreModel).where(
                GenreModel.name == genre_name
            )
        )

        if genre is None:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()

        genres.append(genre)

    # ---------- ACTORS ----------
    actors = []

    for actor_name in movie.actors:
        actor = await db.scalar(
            select(ActorModel).where(
                ActorModel.name == actor_name
            )
        )

        if actor is None:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()

        actors.append(actor)

    # ---------- LANGUAGES ----------
    languages = []

    for language_name in movie.languages:
        language = await db.scalar(
            select(LanguageModel).where(
                LanguageModel.name == language_name
            )
        )

        if language is None:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()

        languages.append(language)

    # ---------- MOVIE ----------
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

    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages

    db.add(new_movie)

    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )

    return result.scalar_one()


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
    status_code=200,
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete(
    "/{movie_id}/",
    status_code=204
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
):
    movie_db = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    if movie_db is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie_db, field, value)

    await db.commit()

    return {
        "detail": "Movie updated successfully."
    }
