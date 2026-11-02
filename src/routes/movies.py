import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud import get_or_create_genres, get_or_create_actors, get_or_create_languages
from database import get_db, MovieModel
from database.models import CountryModel
from schemas import MovieListResponseSchema
from schemas.movies import (
    MovieReturnSchema,
    MovieRequestSchema,
    MovieRequestDetailSchema,
    MoviePatchSchema,
)

router = APIRouter(prefix="/movies", tags=["movies"])


def movie_body(payload: dict) -> MovieRequestSchema:
    try:
        return MovieRequestSchema(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())


def body_for_path(payload: dict = Body(...)) -> MoviePatchSchema:
    try:
        return MoviePatchSchema(**payload)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.patch("/{movie_id}/", status_code=200)
async def patch_movie_with_id(
    movie_id: int,
    payload: MoviePatchSchema = Depends(body_for_path),
    db: AsyncSession = Depends(get_db),
):
    film = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if film is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(film, key, value)

    await db.commit()
    await db.refresh(film)

    return {"detail": "Movie updated successfully."}


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    film = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if film is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(film)
    await db.commit()


@router.get("/{movie_id}/", response_model=MovieRequestDetailSchema, status_code=200)
async def get_movie_details(
    movie_id: int, db: AsyncSession = Depends(get_db)
) -> MovieRequestDetailSchema:
    film = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    if film is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return MovieRequestDetailSchema.model_validate(film)


@router.post("/", response_model=MovieReturnSchema, status_code=201)
async def create_movies(
    payload: MovieRequestSchema = Depends(movie_body),
    db: AsyncSession = Depends(get_db),
):
    if len(payload.name) != 0:
        exists = await db.scalar(
            select(MovieModel).where(
                MovieModel.name == payload.name,
                MovieModel.date == payload.date,
            )
        )
    else:
        raise HTTPException(status_code=400, detail="Name is required")

    if len(payload.name) > 255:
        raise HTTPException(400, detail="Name must be less than 255 characters")

    if payload.date > date.today() + timedelta(days=365):
        raise HTTPException(
            400, f"date{payload.date}—more than one year—into the future."
        )

    if exists:
        raise HTTPException(
            409,
            f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.",
        )
    name = payload.name
    film_date = payload.date

    if payload.score < 0 or payload.score > 100:
        raise HTTPException(400, detail="Score is out of range.")
    score = payload.score
    overview = payload.overview
    status = payload.status

    if payload.budget < 0:
        raise HTTPException(400, detail="Budget is out of range.")
    budget = payload.budget

    if payload.revenue < 0:
        raise HTTPException(400, detail="'Revenue is out of range'")
    revenue = payload.revenue

    if not re.compile(r"^[A-Z]{2,3}$").fullmatch(payload.country):
        raise HTTPException(400, detail="Country is invalid.")

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == payload.country)
    )
    if not country:
        country = CountryModel(code=payload.country)
        db.add(country)
        await db.flush()
    genres = await get_or_create_genres(db, payload.genres)
    actors = await get_or_create_actors(db, payload.actors)
    languages = await get_or_create_languages(db, payload.languages)
    movie = MovieModel(
        name=name,
        date=film_date,
        score=score,
        overview=overview,
        status=status,
        budget=budget,
        revenue=revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie, ["country", "genres", "actors", "languages"])
    return movie


@router.get("/", response_model=MovieListResponseSchema)
async def get_list_movies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    movies = await db.scalars(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    page_movies = movies.all()
    total_items = await db.scalar(
        select(func.count(MovieModel.id)).select_from(MovieModel)
    )
    prev_page = None
    next_page = None

    if not page_movies:
        raise HTTPException(404, "No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=page_movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )
