from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status, responses

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieCreationDetailSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    DetailMessageSchema,
)

router = APIRouter(prefix="/movies")

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


async def get_or_create_entities(db: DatabaseSession, model, names: list[str]) -> list:
    entities = []
    for name in names:
        entity = await db.scalar(select(model).where(model.name == name))
        if not entity:
            entity = model(name=name)
        entities.append(entity)
    return entities


async def get_movie_with_relationships(db: DatabaseSession, movie_id: int):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.unique().scalars().first()
    return movie


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    db: DatabaseSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):

    movies_stmt = select(func.count(MovieModel.id))
    movies_result = await db.execute(movies_stmt)
    movies_count = movies_result.scalar() or 0

    pages_count = (movies_count + per_page - 1) // per_page

    if page > pages_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    movies_stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    movies_result = await db.execute(movies_stmt)
    movies = movies_result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < pages_count
        else None
    )
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": pages_count,
        "total_items": movies_count,
    }


@router.post(
    "/",
    response_model=MovieCreationDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(db: DatabaseSession, movie: MovieCreateSchema):
    duplicate_stmt = select(MovieModel).where(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    )
    duplicate_result = await db.execute(duplicate_stmt)
    duplicate_movie = duplicate_result.scalars().first()
    if duplicate_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country_stmt = select(CountryModel).where(CountryModel.code == movie.country)
    country_result = await db.execute(country_stmt)
    country = country_result.scalars().first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)

    genres = await get_or_create_entities(db, GenreModel, movie.genres)
    actors = await get_or_create_entities(db, ActorModel, movie.actors)
    languages = await get_or_create_entities(db, LanguageModel, movie.languages)

    new_movie = MovieModel(
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
    db.add(new_movie)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    movie_with_relations = await get_movie_with_relationships(
        db=db, movie_id=new_movie.id
    )
    return movie_with_relations


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: DatabaseSession):
    movie_with_relations = await get_movie_with_relationships(db, movie_id)
    if not movie_with_relations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie_with_relations


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: DatabaseSession):
    delete_stmt = select(MovieModel).where(MovieModel.id == movie_id)
    delete_result = await db.execute(delete_stmt)
    movie_for_delete = delete_result.scalars().first()
    if not movie_for_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    await db.delete(movie_for_delete)
    await db.commit()
    return responses.Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/", response_model=DetailMessageSchema)
async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: DatabaseSession):
    update_stmt = select(MovieModel).where(MovieModel.id == movie_id)
    update_result = await db.execute(update_stmt)
    movie_for_update = update_result.scalars().first()

    if not movie_for_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    print()
    for key, value in movie.model_dump(exclude_unset=True).items():
        setattr(movie_for_update, key, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )

    return DetailMessageSchema(detail="Movie updated successfully.")
