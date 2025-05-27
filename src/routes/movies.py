from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from database.session_sqlite import get_sqlite_db
from schemas.movies import (
    MovieCreate,
    MovieListResponseSchema,
    MovieDetailSchema,
)
from pydantic import ValidationError

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_sqlite_db)
):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = (total_items + per_page - 1) // per_page if total_items else 0

    if page > total_pages and total_items != 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    def get_page_url(p: int) -> Optional[str]:
        if 1 <= p <= total_pages:
            return f"/movies/?page={p}&per_page={per_page}"
        return None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=get_page_url(page - 1) if page > 1 else None,
        next_page=get_page_url(page + 1) if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MovieDetailSchema)
async def create_movie(movie: MovieCreate, db: AsyncSession = Depends(get_sqlite_db)):
    existing_stmt = select(MovieModel).where(
        and_(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    existing = await db.execute(existing_stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country_stmt = select(CountryModel).where(CountryModel.code == movie.country)
    country_result = await db.execute(country_stmt)
    country = country_result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie.country, name=None)
        db.add(country)
        await db.flush()

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
    )

    for genre_name in movie.genres:
        genre_stmt = select(GenreModel).where(GenreModel.name == genre_name)
        genre_res = await db.execute(genre_stmt)
        genre = genre_res.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.flush()
        new_movie.genres.append(genre)

    for actor_name in movie.actors:
        actor_stmt = select(ActorModel).where(ActorModel.name == actor_name)
        actor_res = await db.execute(actor_stmt)
        actor = actor_res.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.flush()
        new_movie.actors.append(actor)

    for lang_name in movie.languages:
        lang_stmt = select(LanguageModel).where(LanguageModel.name == lang_name)
        lang_res = await db.execute(lang_stmt)
        language = lang_res.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=lang_name)
            db.add(language)
            await db.flush()
        new_movie.languages.append(language)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return new_movie


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(
    movie_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_sqlite_db)
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
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_sqlite_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()

    return


@router.patch("/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int = Path(..., ge=1),
    movie_data: dict = None,
    db: AsyncSession = Depends(get_sqlite_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")


    from pydantic import BaseModel, ValidationError, constr, confloat, condecimal, validator

    class MovieUpdateSchema(BaseModel):
        name: Optional[constr(max_length=255)]
        date: Optional[datetime]
        score: Optional[confloat(ge=0, le=100)]
        overview: Optional[str]
        status: Optional[constr(regex="^(Released|Post Production|In Production)$")]
        budget: Optional[condecimal(ge=0)]
        revenue: Optional[condecimal(ge=0)]

        @validator("date")
        def date_not_more_than_one_year_in_future(cls, v):
            if v and v.date() > (datetime.utcnow().date() + timedelta(days=365)):
                raise ValueError('date must not be more than one year in the future')
            return v

    try:
        update_obj = MovieUpdateSchema(**movie_data)
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for field, value in update_obj.dict(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}
