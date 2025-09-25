import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import (
    MovieCreateSchema,
    MovieCreateResponseSchema,
    MovieUpdateSchema,
    CountrySchema,
    ItemSchema,
)


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def read_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    total_items = await db.scalar(
        select(func.count()).select_from(MovieModel)
    )

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(status_code=404, detail="Page out of range")

    base = "/theater/movies/"
    prev_page = (
        f"{base}?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"{base}?page={page + 1}&per_page={per_page}" if page < total_pages else None
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
    response_model=MovieDetailSchema
)
async def read_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
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

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    country = (
        CountrySchema(
            id=movie.country.id,
            name=movie.country.name,
            code=movie.country.code,
        )
        if movie.country
        else None
    )

    return MovieDetailSchema(
        id=movie_id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=[{"id": genre.id, "name": genre.name} for genre in movie.genres],
        actors=[{"id": actor.id, "name": actor.name} for actor in movie.actors],
        languages=[{"id": language.id, "name": language.name} for language in movie.languages],
    )


@router.post(
    "/movies/",
    response_model=MovieCreateResponseSchema,
    status_code=201
)
async def add_movie(
    movie: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(MovieModel).where(
            and_(MovieModel.name == movie.name, MovieModel.date == movie.date)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie.name}' "
                f"and release date '{movie.date}' already exists."
            ),
        )

    country_result = await db.execute(
        select(CountryModel).where(CountryModel.name == movie.country)
    )
    country_obj = country_result.scalar_one_or_none() or CountryModel(
        name=movie.country, code="US"
    )
    db.add(country_obj)

    genres = []
    for genre_name in movie.genres:
        genre_result = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        genre_obj = genre_result.scalar_one_or_none() or GenreModel(name=genre_name)
        db.add(genre_obj)
        genres.append(genre_obj)

    actors = []
    for actor_name in movie.actors:
        actor_result = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        actor_obj = actor_result.scalar_one_or_none() or ActorModel(name=actor_name)
        db.add(actor_obj)
        actors.append(actor_obj)

    languages = []
    for language_name in movie.languages:
        lang_result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == language_name)
        )
        language_obj = lang_result.scalar_one_or_none() or LanguageModel(name=language_name)
        db.add(language_obj)
        languages.append(language_obj)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country_obj,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(new_movie)
    await db.commit()

    statement = select(MovieModel).options(
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
        selectinload(MovieModel.country),
    ).where(MovieModel.id == new_movie.id)
    result = await db.execute(statement)
    new_movie = result.scalar_one()

    return MovieCreateResponseSchema(
        id=new_movie.id,
        name=new_movie.name,
        date=new_movie.date,
        score=new_movie.score,
        overview=new_movie.overview,
        status=new_movie.status,
        budget=new_movie.budget,
        revenue=new_movie.revenue,
        country=(
            CountrySchema(
                id=new_movie.country.id,
                name=new_movie.country.name,
                code=new_movie.country.code,
            )
            if new_movie.country
            else None
        ),
        genres=[ItemSchema(id=g.id, name=g.name) for g in new_movie.genres],
        actors=[ItemSchema(id=a.id, name=a.name) for a in new_movie.actors],
        languages=[ItemSchema(id=language.id, name=language.name) for language in new_movie.languages],
    )


@router.delete(
    "/movies/{movie_id}/",
    status_code=204
)
async def remove_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.execute(delete(MovieModel).where(MovieModel.id == movie_id))
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    status_code=200
)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    if movie_data.name is not None:
        movie.name = movie_data.name
    if movie_data.date is not None:
        movie.date = movie_data.date
    if movie_data.score is not None:
        movie.score = movie_data.score
    if movie_data.overview is not None:
        movie.overview = movie_data.overview
    if movie_data.status is not None:
        movie.status = movie_data.status
    if movie_data.budget is not None:
        movie.budget = movie_data.budget
    if movie_data.revenue is not None:
        movie.revenue = movie_data.revenue

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
