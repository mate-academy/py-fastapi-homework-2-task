from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import MovieModel, get_db
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


router = APIRouter(prefix="/movies")


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    if total_items == 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found.",
        )

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found.",
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


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    country_result = await db.execute(
        select(CountryModel).where(
            CountryModel.code == movie_data.country
        )
    )
    country = country_result.scalar_one_or_none()

    if country is None:
        country = CountryModel(
            code=movie_data.country,
            name=movie_data.country,
        )
        db.add(country)
        await db.flush()

    genres = []

    for genre_name in movie_data.genres:
        result = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre = result.scalar_one_or_none()

        if genre is None:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()

        genres.append(genre)

    actors = []

    for actor_name in movie_data.actors:
        result = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        actor = result.scalar_one_or_none()

        if actor is None:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()

        actors.append(actor)

    languages = []

    for language_name in movie_data.languages:
        result = await db.execute(
            select(LanguageModel).where(
                LanguageModel.name == language_name
            )
        )
        language = result.scalar_one_or_none()

        if language is None:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()

        languages.append(language)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )

    return result.scalar_one()


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()

        if "unique_movie_constraint" in str(exc):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"A movie with the name '{movie.name}' "
                    f"and release date '{movie.date}' already exists."
                ),
            )

        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    return {"detail": "Movie updated successfully."}


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()

    return None
