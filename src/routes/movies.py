import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from src.schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateResponseSchema, \
    MovieUpdateSchema

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    count_query = select(func.count(MovieModel.id))
    result = await db.execute(count_query)
    total_items = result.scalar()

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    duplicate_query = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    )
    result = await db.execute(duplicate_query)
    existing_movie = result.scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country_query = select(CountryModel).where(CountryModel.code == movie_data.country)
    result = await db.execute(country_query)
    country = result.scalar_one_or_none()

    if not country:
        country = CountryModel(code=movie_data.country, name=None)
        db.add(country)
        await db.flush()

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status.value,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id
    )

    for genre_name in movie_data.genres:
        genre_query = select(GenreModel).where(GenreModel.name == genre_name)
        result = await db.execute(genre_query)
        genre = result.scalar_one_or_none()

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()

        new_movie.genres.append(genre)

    for actor_name in movie_data.actors:
        actor_query = select(ActorModel).where(ActorModel.name == actor_name)
        result = await db.execute(actor_query)
        actor = result.scalar_one_or_none()

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()

        new_movie.actors.append(actor)

    for language_name in movie_data.languages:
        language_query = select(LanguageModel).where(LanguageModel.name == language_name)
        result = await db.execute(language_query)
        language = result.scalar_one_or_none()

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()

        new_movie.languages.append(language)

    db.add(new_movie)
    await db.commit()

    query = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
    )
    result = await db.execute(query)
    created_movie = result.scalar_one()

    return created_movie


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
    )
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return None


@router.patch("/{movie_id}/", response_model=MovieUpdateResponseSchema)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "status" and value is not None:
            setattr(movie, field, value.value)
        else:
            setattr(movie, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    return MovieUpdateResponseSchema(detail="Movie updated successfully.")