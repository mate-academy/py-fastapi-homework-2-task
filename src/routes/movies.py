from datetime import date, timedelta
from typing import List, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
from schemas.movies import (
    MovieListResponse,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    CountrySchema,
    RelatedItemSchema
)


router = APIRouter()


async def _get_or_create_single(
    db: AsyncSession,
    model,
    unique_field: str,
    value: str
):
    """
    Fetch a single related object or create it if it does not exist.
    """
    stmt = select(model).where(getattr(model, unique_field) == value)
    result = await db.execute(stmt)
    instance = result.scalars().first()
    if instance:
        return instance

    instance = model(**{unique_field: value})
    db.add(instance)
    await db.flush()
    return instance


async def _get_or_create_multiple(
    db: AsyncSession,
    model,
    unique_field: str,
    values: List[str]
):
    """
    Fetch or create multiple related objects and return them as a list.
    """
    if not values:
        return []

    unique_values = list(dict.fromkeys(values))
    stmt = select(model).where(getattr(model, unique_field).in_(unique_values))
    result = await db.execute(stmt)
    existing_items = {getattr(item, unique_field): item for item in result.scalars().all()}

    for value in unique_values:
        if value not in existing_items:
            new_item = model(**{unique_field: value})
            db.add(new_item)
            await db.flush()
            existing_items[value] = new_item

    return list(existing_items.values())


async def _get_movie_with_relations(db: AsyncSession, movie_id: int) -> MovieModel | None:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


def _build_detail_schema(movie: MovieModel) -> MovieDetailSchema:
    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=float(movie.budget),
        revenue=movie.revenue,
        country=CountrySchema(id=movie.country.id, code=movie.country.code, name=movie.country.name),
        genres=[RelatedItemSchema(id=genre.id, name=genre.name) for genre in movie.genres],
        actors=[RelatedItemSchema(id=actor.id, name=actor.name) for actor in movie.actors],
        languages=[RelatedItemSchema(id=language.id, name=language.name) for language in movie.languages],
    )


@router.get("/movies/", response_model=MovieListResponse)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
) -> MovieListResponse:
    total_stmt = select(func.count(MovieModel.id))
    total_result = await db.execute(total_stmt)
    total_items = total_result.scalar_one()

    offset = (page - 1) * per_page
    if total_items == 0 or offset >= total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies_stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(movies_stmt)
    movies: Sequence[MovieModel] = result.scalars().all()

    total_pages = (total_items + per_page - 1) // per_page

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    movie_items = [
        MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
        )
        for movie in movies
    ]

    return MovieListResponse(
        movies=movie_items,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    movie = await _get_movie_with_relations(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return _build_detail_schema(movie)


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    if (
        movie_data.name is None
        or movie_data.date is None
        or movie_data.score is None
        or movie_data.overview is None
        or movie_data.status is None
        or movie_data.budget is None
        or movie_data.revenue is None
        or movie_data.country is None
    ):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if len(movie_data.name) > 255:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie_data.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if not (0 <= movie_data.score <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie_data.budget < 0 or movie_data.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    try:
        status_value = MovieStatusEnum(movie_data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    country = await _get_or_create_single(db, CountryModel, "code", movie_data.country)
    genres = await _get_or_create_multiple(db, GenreModel, "name", movie_data.genres)
    actors = await _get_or_create_multiple(db, ActorModel, "name", movie_data.actors)
    languages = await _get_or_create_multiple(db, LanguageModel, "name", movie_data.languages)

    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=status_value,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id,
    )
    movie.genres = genres
    movie.actors = actors
    movie.languages = languages

    db.add(movie)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists.",
        )

    created_movie = await _get_movie_with_relations(db, movie.id)
    if created_movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return _build_detail_schema(created_movie)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if movie_data.name is not None:
        if len(movie_data.name) > 255:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.name = movie_data.name

    if movie_data.date is not None:
        movie.date = movie_data.date

    if movie_data.score is not None:
        if not (0 <= movie_data.score <= 100):
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.score = movie_data.score

    if movie_data.overview is not None:
        movie.overview = movie_data.overview

    if movie_data.status is not None:
        try:
            movie.status = MovieStatusEnum(movie_data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie_data.budget is not None:
        if movie_data.budget < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.budget = movie_data.budget

    if movie_data.revenue is not None:
        if movie_data.revenue < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")
        movie.revenue = movie_data.revenue

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
