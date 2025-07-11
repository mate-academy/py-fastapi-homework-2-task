from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema, MovieCreateRequestSchema, MovieUpdateRequestSchema, MovieListItemSchema
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/movies", tags=["Movies"])

@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    total_items = (await db.execute(select(func.count()).select_from(MovieModel))).scalar()
    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages and total_items != 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/movies/"
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page+1}&per_page={per_page}" if page < total_pages else None
    movie_schemas = [
        MovieListItemSchema.model_validate(movie)
        for movie in movies
    ]

    return MovieListResponseSchema(
        movies=movie_schemas,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )

@router.post("/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_movie(data: MovieCreateRequestSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).filter_by(name=data.name, date=data.date))
    duplicate = result.scalars().first()
    if duplicate:
        raise HTTPException(status_code=409, detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists.")

    if data.date > datetime.today().date() + timedelta(days=365):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(select(CountryModel).filter_by(code=data.country))
    country = result.scalars().first()
    if not country:
        country = CountryModel(code=data.country, name=None)
        db.add(country)
        await db.flush()

    genres, actors, languages = [], [], []

    for g in data.genres:
        result = await db.execute(select(GenreModel).filter_by(name=g))
        genre = result.scalars().first()
        if not genre:
            genre = GenreModel(name=g)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    for a in data.actors:
        result = await db.execute(select(ActorModel).filter_by(name=a))
        actor = result.scalars().first()
        if not actor:
            actor = ActorModel(name=a)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    for l in data.languages:
        result = await db.execute(select(LanguageModel).filter_by(name=l))
        lang = result.scalars().first()
        if not lang:
            lang = LanguageModel(name=l)
            db.add(lang)
            await db.flush()
        languages.append(lang)

    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie

@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(joinedload(MovieModel.country))
        .options(joinedload(MovieModel.genres))
        .options(joinedload(MovieModel.actors))
        .options(joinedload(MovieModel.languages))
        .filter_by(id=movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie

@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).filter_by(id=movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()
    return

@router.patch("/{movie_id}/")
async def update_movie(movie_id: int, data: MovieUpdateRequestSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).filter_by(id=movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    if data.score is not None and not (0 <= data.score <= 100):
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if data.budget is not None and data.budget < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")
    if data.revenue is not None and data.revenue < 0:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
