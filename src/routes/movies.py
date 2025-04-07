from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import date, timedelta
from typing import List
from pydantic import ValidationError

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieBase,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MovieUpdate
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_list(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page
    total_items_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_result.scalar_one()
    total_pages = (total_items + per_page - 1) // per_page

    if total_items > 0 and page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies_result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = movies_result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list_items = [
        MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview
        )
        for movie in movies
    ]

    return MovieListResponseSchema(
        movies=movie_list_items,
        prev_page=f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items
    )


async def get_or_create_country(db: AsyncSession, code: str):
    result = await db.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=code)
        db.add(country)
        await db.commit()
        await db.refresh(country)
    return country


async def get_or_create_genres(db: AsyncSession, genre_names: List[str]):
    genres = []
    for name in genre_names:
        result = await db.execute(select(GenreModel).where(GenreModel.name == name))
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.commit()
            await db.refresh(genre)
        genres.append(genre)
    return genres


async def get_or_create_actors(db: AsyncSession, actor_names: List[str]):
    actors = []
    for name in actor_names:
        result = await db.execute(select(ActorModel).where(ActorModel.name == name))
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.commit()
            await db.refresh(actor)
        actors.append(actor)
    return actors


async def get_or_create_languages(db: AsyncSession, language_names: List[str]):
    languages = []
    for name in language_names:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == name))
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.commit()
            await db.refresh(language)
        languages.append(language)
    return languages


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieBase, db: AsyncSession = Depends(get_db)):
    try:
        if movie_data.date > date.today() + timedelta(days=365):
            raise HTTPException(
                status_code=400,
                detail="Release date cannot be more than one year in the future."
            )

        existing_movie = await db.execute(
            select(MovieModel)
            .where(MovieModel.name == movie_data.name)
            .where(MovieModel.date == movie_data.date)
        )
        if existing_movie.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
            )

        country = await get_or_create_country(db, movie_data.country)
        genres = await get_or_create_genres(db, movie_data.genres)
        actors = await get_or_create_actors(db, movie_data.actors)
        languages = await get_or_create_languages(db, movie_data.languages)

        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status.value,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country_id=country.id
        )

        movie.genres.extend(genres)
        movie.actors.extend(actors)
        movie.languages.extend(languages)

        db.add(movie)
        await db.commit()
        await db.refresh(movie)

        movie_with_relations = await db.execute(
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages)
            )
            .where(MovieModel.id == movie.id)
        )
        movie_with_relations = movie_with_relations.scalar_one()

        return movie_with_relations
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    movie = movie.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch(
    "/movies/{movie_id}/",
    responses={
        200: {
            "description": "Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie updated successfully."}
                }
            },
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."}
                }
            },
        },
    }
)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdate,
        db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    try:
        update_fields = movie_data.model_dump(exclude_unset=True)
        validated_data = MovieUpdate(**update_fields)
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Validation failed: {e.errors()}"
        )

    for field, value in validated_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
