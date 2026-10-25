from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
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


router = APIRouter()


@router.get(
    "/movies/",
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


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    movie = result.unique().scalars().first()

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    existing_movie = result.scalars().first()

    if existing_movie is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    result = await db.execute(
        select(CountryModel).where(
            CountryModel.code == movie_data.country
        )
    )
    country = result.scalars().first()

    if country is None:
        country = CountryModel(
            code=movie_data.country,
        )
        db.add(country)
        await db.flush()

    genres = []

    for genre_name in movie_data.genres:
        result = await db.execute(
            select(GenreModel).where(
                GenreModel.name == genre_name
            )
        )
        genre = result.scalars().first()

        if genre is None:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()

        genres.append(genre)

    actors = []

    for actor_name in movie_data.actors:
        result = await db.execute(
            select(ActorModel).where(
                ActorModel.name == actor_name
            )
        )
        actor = result.scalars().first()

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
        language = result.scalars().first()

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
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )

    return result.unique().scalars().first()


@router.delete(
    "/movies/{movie_id}/",
    status_code=204,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()

    return {
        "detail": "Movie updated successfully.",
    }
