import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas import (
    PaginatedMoviesResponse,
    MovieCreate,
    MovieDetailOut,
    MovieUpdate
)

router = APIRouter()


@router.get("/movies/", response_model=PaginatedMoviesResponse)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    total_items_query = select(func.count(MovieModel.id))
    total_items_result = await db.execute(total_items_query)
    total_items = total_items_result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    movies_query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies_result = await db.execute(movies_query)
    movies = movies_result.scalars().all()

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailOut, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreate, db: AsyncSession = Depends(get_db)):
    duplicate_query = select(MovieModel).filter_by(name=movie_data.name, date=movie_data.date)
    duplicate_res = await db.execute(duplicate_query)
    if duplicate_res.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country_query = select(CountryModel).filter_by(code=movie_data.country)
    country_res = await db.execute(country_query)
    country = country_res.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie_data.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for g_name in movie_data.genres:
        g_query = select(GenreModel).filter_by(name=g_name)
        g_res = await db.execute(g_query)
        genre = g_res.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=g_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for a_name in movie_data.actors:
        a_query = select(ActorModel).filter_by(name=a_name)
        a_res = await db.execute(a_query)
        actor = a_res.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=a_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for l_name in movie_data.languages:
        l_query = select(LanguageModel).filter_by(name=l_name)
        l_res = await db.execute(l_query)
        lang = l_res.scalar_one_or_none()
        if not lang:
            lang = LanguageModel(name=l_name)
            db.add(lang)
        languages.append(lang)

    await db.flush()

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages
    )

    db.add(new_movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .filter_by(id=new_movie.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/movies/{movie_id}/", response_model=MovieDetailOut)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .filter_by(id=movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).filter_by(id=movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None



@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie_data: MovieUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).filter_by(id=movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
