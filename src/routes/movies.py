from datetime import date, timedelta

from fastapi import APIRouter, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette import status

from database.session_postgresql import get_postgresql_db as get_session
from schemas.movies import MovieSchema, MoviesListResponse, MovieResponseSchema, MovieCreateSchema
from typing import Optional
from fastapi import Depends
from database.models import MovieModel, GenreModel, CountryModel, ActorModel, LanguageModel

import math

router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)


@router.get("/", response_model=MoviesListResponse)
async def list_movies(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):

    total_items_result = await session.execute(select(MovieModel))
    total_items = total_items_result.scalars().all()
    total_items_count = len(total_items)

    if total_items_count == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items_count / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    stmt = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    movies = result.scalars().all()

    base_url = str(request.url_for("list_movies"))

    def build_page_url(page_num: int) -> Optional[str]:
        if page_num < 1 or page_num > total_pages:
            return None
        return f"{base_url}?page={page_num}&per_page={per_page}"

    prev_page = build_page_url(page - 1) if page > 1 else None
    next_page = build_page_url(page + 1) if page < total_pages else None

    return MoviesListResponse(
        movies=[
            MovieSchema(
                id=movie.id,
                name=movie.name,
                date=str(movie.date),
                score=movie.score,
                overview=movie.overview
            )
            for movie in movies
        ],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items_count
    )


@router.post("/", response_model=MovieResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie_data: MovieCreateSchema, session: AsyncSession = Depends(get_session)):
    # 1. Перевірка дублікату фільму (по name і date)
    existing_movie = await session.execute(
        select(MovieModel).where(MovieModel.name == movie_data.name, MovieModel.date == movie_data.date)
    )
    if existing_movie.scalar():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # 2. Валідація даних
    if len(movie_data.name) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be <= 255 characters.")
    if movie_data.date > date.today() + timedelta(days=365):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date must not be more than 1 year in the future.")
    if not (0 <= movie_data.score <= 100):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score must be between 0 and 100.")
    if movie_data.budget < 0 or movie_data.revenue < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Budget and revenue must be non-negative.")

    # 3. Пошук або створення країни
    result = await session.execute(select(CountryModel).where(CountryModel.code == movie_data.country))
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=movie_data.country)
        session.add(country)
        await session.flush()

    # 4. Пошук або створення жанрів
    genres = []
    for genre_name in movie_data.genres:
        result = await session.execute(select(GenreModel).where(GenreModel.name == genre_name))
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=genre_name)
            session.add(genre)
            await session.flush()
        genres.append(genre)

    # 5. Пошук або створення акторів
    actors = []
    for actor_name in movie_data.actors:
        result = await session.execute(select(ActorModel).where(ActorModel.name == actor_name))
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=actor_name)
            session.add(actor)
            await session.flush()
        actors.append(actor)

    # 6. Пошук або створення мов
    languages = []
    for language_name in movie_data.languages:
        result = await session.execute(select(LanguageModel).where(LanguageModel.name == language_name))
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=language_name)
            session.add(language)
            await session.flush()
        languages.append(language)

    # 7. Створення фільму
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
        languages=languages,
    )

    session.add(new_movie)
    await session.commit()
    await session.refresh(new_movie)

    return new_movie



@router.get("/{movie_id}/", response_model=MovieSchema)
async def get_movie(movie_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return MovieSchema.from_orm(movie)


# Delete movie endpoint
@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await session.delete(movie)
    await session.commit()

    return

# PATCH endpoint to update a movie
from pydantic import BaseModel

class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    class Config:
        orm_mode = True

@router.patch("/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_fields = movie_data.dict(exclude_unset=True)

    if "name" in update_fields and len(update_fields["name"]) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be <= 255 characters.")
    if "date" in update_fields and update_fields["date"] > date.today() + timedelta(days=365):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Date must not be more than 1 year in the future.")
    if "score" in update_fields and not (0 <= update_fields["score"] <= 100):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Score must be between 0 and 100.")
    if "budget" in update_fields and update_fields["budget"] < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Budget must be non-negative.")
    if "revenue" in update_fields and update_fields["revenue"] < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Revenue must be non-negative.")

    for field, value in update_fields.items():
        setattr(movie, field, value)

    session.add(movie)
    await session.commit()

    return {"detail": "Movie updated successfully."}
