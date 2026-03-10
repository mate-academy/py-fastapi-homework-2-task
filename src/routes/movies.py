import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieStatusEnum,
)
from schemas.movies import (
    MoviePaginationResponse,
    MovieCreate,
    MovieDetail,
    MovieUpdate,
)

router = APIRouter()


@router.get("/movies/", response_model=MoviePaginationResponse)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    query = (
        select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page)
    )
    movies = (await db.scalars(query)).all()

    base_url = "/theater/movies"
    prev_page = f"{base_url}/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = (
        f"{base_url}/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieDetail, status_code=201)
async def create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db)):
    duplicate_query = select(MovieModel).where(
        MovieModel.name == movie_in.name, MovieModel.date == movie_in.date
    )
    existing_movie = await db.scalar(duplicate_query)
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists.",
        )

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie_in.country)
    )
    if not country:
        country = CountryModel(code=movie_in.country, name=None)
        db.add(country)
        await db.flush()

    async def get_or_create_related(model, names: list[str]):
        objects = []
        for name in names:
            obj = await db.scalar(select(model).where(model.name == name))
            if not obj:
                obj = model(name=name)
                db.add(obj)
            objects.append(obj)
        return objects

    genres_objs = await get_or_create_related(GenreModel, movie_in.genres)
    actors_objs = await get_or_create_related(ActorModel, movie_in.actors)
    languages_objs = await get_or_create_related(LanguageModel, movie_in.languages)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=MovieStatusEnum(movie_in.status),
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country_id=country.id,
        genres=genres_objs,
        actors=actors_objs,
        languages=languages_objs,
    )

    db.add(new_movie)
    try:
        await db.commit()
        await db.refresh(new_movie)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    movie = result.scalar_one()

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):

    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    movie = await db.scalar(query)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):

    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_in: MovieUpdate,
    db: AsyncSession = Depends(get_db),
):

    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
