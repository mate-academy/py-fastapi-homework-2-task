import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload

if os.environ.get("ENVIRONMENT") == "testing":
    from src.database.session_sqlite import get_sqlite_db as get_db
else:
    from src.database.session_postgresql import get_postgresql_db as get_db

from src.database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    CountryModel,
)
from src.schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieFull,
    MovieListResponseSchema,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    count_query = select(func.count()).select_from(MovieModel)
    total_items = (await db.execute(count_query)).scalar()

    query = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/theater/movies/"

    prev_p = f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None
    next_p = (
        f"{base_url}?page={page+1}&per_page={per_page}" if page < total_pages else None
    )

    return {
        "movies": movies,
        "prev_page": prev_p,
        "next_page": next_p,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", response_model=MovieFull, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_in.name, MovieModel.date == movie_in.date
        )
    )
    if existing.scalar():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists.",
        )

    async def get_or_create(model, field, values):
        entities = []
        for val in values:
            res = await db.execute(select(model).where(getattr(model, field) == val))
            item = res.scalar()
            if not item:
                item = model(**{field: val})
                db.add(item)
            entities.append(item)
        return entities

    country_res = await db.execute(
        select(CountryModel).where(CountryModel.code == movie_in.country)
    )
    country = country_res.scalar()
    if not country:
        country = CountryModel(code=movie_in.country, name=None)
        db.add(country)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country,
        genres=await get_or_create(GenreModel, "name", movie_in.genres),
        actors=await get_or_create(ActorModel, "name", movie_in.actors),
        languages=await get_or_create(LanguageModel, "name", movie_in.languages),
    )

    db.add(new_movie)
    await db.commit()

    query = (
        select(MovieModel)
        .where(MovieModel.id == new_movie.id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
    )
    result = await db.execute(query)
    return result.scalar_one()


@router.get("/{movie_id}/", response_model=MovieFull)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        )
    )
    result = await db.execute(query)
    movie = result.scalar()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/", response_model=dict)
async def update_movie(
    movie_id: int, movie_in: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
