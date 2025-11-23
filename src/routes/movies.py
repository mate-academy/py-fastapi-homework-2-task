import datetime
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListItemSchema, MovieDetailSchema
from schemas.movies import MovieUpdateSchema, MovieCreateSchema

router = APIRouter()


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    duplicate_query = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    existing_movie = duplicate_query.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    if (
        len(movie.name) > 255
        or movie.score < 0
        or movie.score > 100
        or movie.budget < 0
        or movie.revenue < 0
        or movie.date > (datetime.date.today() + timedelta(days=365))
    ):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    country_obj = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )

    if not country_obj:
        country_obj = CountryModel(code=movie.country)
        db.add(country_obj)
        await db.flush()

    genre_objs = []
    for genre_name in movie.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))

        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        genre_objs.append(genre)

    actor_objs = []
    for actor_name in movie.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))

        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        actor_objs.append(actor)

    language_objs = []
    for language_name in movie.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == language_name)
        )

        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.flush()
        language_objs.append(language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country_obj,
    )
    new_movie.genres = genre_objs
    new_movie.actors = actor_objs
    new_movie.languages = language_objs

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    new_movie_loaded = result.scalar_one()

    return new_movie_loaded


@router.get("/movies/", response_model=MovieListItemSchema)
async def get_movies(
    page: int = Query(1, ge=1, description="Page number (must be >= 1)"),
    per_page: int = Query(10, ge=1, le=20, description="Items per page (1–20)"),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MovieModel)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if len(movies) < 1:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    total_pages = (total_items + per_page - 1) // per_page

    return {
        "movies": movies,
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
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
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
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
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(
    movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
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
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    if movie.score is not None:
        if movie.score > 100 or movie.score < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie.budget is not None:
        if movie.budget < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    if movie.revenue is not None:
        if movie.revenue < 0:
            raise HTTPException(status_code=400, detail="Invalid input data.")

    update_data = movie.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)
    return {"detail": "Movie updated successfully."}
