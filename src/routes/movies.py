import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

import schemas
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreate, MessageResponse, MovieUpdate, MovieDetailSchema

router = APIRouter()

MoviePostResponse = MovieDetailSchema


@router.get(
    "/movies/",
    response_model=schemas.movies.MovieListResponseSchema
)
async def movies_get(
        request: Request,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
        db: AsyncSession = Depends(get_db)
):
    base_endpoint = request.url.path.removeprefix("/api/v1")

    count_stmt = select(func.count()).select_from(MovieModel)
    total_items_res = await db.execute(count_stmt)
    total_items = total_items_res.scalar_one()

    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

    offset_val = (page - 1) * per_page
    query = select(MovieModel).offset(offset_val).limit(per_page).order_by(MovieModel.id.desc())
    res = await db.execute(query)
    movies = res.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    prev_page = (
        f"{base_endpoint}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )

    next_page = (
        f"{base_endpoint}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return schemas.movies.MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MoviePostResponse,
    status_code=status.HTTP_200_OK,
)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


async def get_or_create_items(db: AsyncSession, model, names: list[str]):
    items = []
    for name in names:
        stmt = select(model).where(model.name == name)
        result = await db.execute(stmt)
        instance = result.scalars().first()

        if not instance:
            instance = model(name=name)
            db.add(instance)
            await db.flush()

        items.append(instance)
    return items


@router.post(
    "/movies/",
    response_model=MoviePostResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie_in: MovieCreate,
    db: AsyncSession = Depends(get_db)
):
    existing_movie_stmt = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date,
    )
    existing_movie_res = await db.execute(existing_movie_stmt)
    if existing_movie_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    stmt_country = select(CountryModel).where(CountryModel.code == movie_in.country)
    res_country = await db.execute(stmt_country)
    country_obj = res_country.scalars().first()

    if not country_obj:
        country_obj = CountryModel(code=movie_in.country)
        db.add(country_obj)
        await db.flush()

    genres_objs = await get_or_create_items(db, GenreModel, movie_in.genres)
    actors_objs = await get_or_create_items(db, ActorModel, movie_in.actors)
    languages_objs = await get_or_create_items(db, LanguageModel, movie_in.languages)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country_obj,
        genres=genres_objs,
        actors=actors_objs,
        languages=languages_objs,
    )

    db.add(new_movie)
    await db.commit()

    await db.refresh(
        new_movie,
        attribute_names=["country", "genres", "actors", "languages"]
    )

    return new_movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()

    return None


@router.patch(
    "/movies/{movie_id}/",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
