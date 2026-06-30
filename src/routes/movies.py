import math
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload

# from database.session_sqlite import get_sqlite_db as get_db
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    PaginatedMoviesResponse, MovieCreateRequest, MovieDetailedResponse, MovieUpdateRequest
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=PaginatedMoviesResponse)
async def get_movies(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    total_items_query = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_query.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page
    movies_query = await db.execute(
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    movies = movies_query.scalars().all()

    base_url = str(request.url.path).replace("/api/v1", "")
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/", response_model=MovieDetailedResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreateRequest, db: AsyncSession = Depends(get_db)):
    existing_query = await db.execute(
        select(MovieModel).where(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    )
    if existing_query.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    country_query = await db.execute(select(CountryModel).where(CountryModel.code == movie_data.country))
    country = country_query.scalars().first()
    if not country:
        country = CountryModel(code=movie_data.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for g_name in movie_data.genres:
        g_query = await db.execute(select(GenreModel).where(GenreModel.name == g_name))
        genre = g_query.scalars().first()
        if not genre:
            genre = GenreModel(name=g_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for a_name in movie_data.actors:
        a_query = await db.execute(select(ActorModel).where(ActorModel.name == a_name))
        actor = a_query.scalars().first()
        if not actor:
            actor = ActorModel(name=a_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for l_name in movie_data.languages:
        l_query = await db.execute(select(LanguageModel).where(LanguageModel.name == l_name))
        language = l_query.scalars().first()
        if not language:
            language = LanguageModel(name=l_name)
            db.add(language)
        languages.append(language)

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
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country)
        )
    )

    return result.scalars().first()


@router.get("/{movie_id}/", response_model=MovieDetailedResponse)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country)
        )
    )
    result = await db.execute(query)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/{movie_id}/")
async def update_movie(movie_id: int, update_data: MovieUpdateRequest, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    data_to_update = update_data.model_dump(exclude_unset=True)
    if not data_to_update:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in data_to_update.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
