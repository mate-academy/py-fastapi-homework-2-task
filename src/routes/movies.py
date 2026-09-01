import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, Session
from starlette import status

from database import get_db
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieModel
from schemas.movies import (
    MessageResponseSchema,
    MovieUpdateSchema,
    MovieCreateSchema,
    MovieListResponseSchema,
    MovieDetailSchema
)

router = APIRouter()


async def get_or_create_country(
        db: AsyncSession,
        code: str
) -> CountryModel:
    result = await db.execute(
        select(CountryModel).where(CountryModel.code == code)
    )
    country = result.scalars().first()
    if country is None:
        country = CountryModel(code=code)
        db.add(country)
        await db.flush()
    return country


async def _get_or_create_genres(
        db: AsyncSession,
        names: list[str]
) -> list[GenreModel]:
    genres = []
    for name in names:
        result = await db.execute(
            select(GenreModel).where(GenreModel.name == name)
        )
        genre = result.scalars().first()
        if genre is None:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)
    return genres


async def _get_or_create_actors(
        db: AsyncSession,
        names: list[str]
) -> list[ActorModel]:
    actors = []
    for name in names:
        result = await db.execute(
            select(ActorModel).where(ActorModel.name == name)
        )
        actor = result.scalars().first()
        if actor is None:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    return actors


async def _get_or_create_languages(
        db: AsyncSession,
        names: list[str]
) -> list[LanguageModel]:
    languages = []
    for name in names:
        result = await db.execute(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        language = result.scalars().first()
        if language is None:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    return languages


async def _get_movie_or_404(
        db: AsyncSession,
        movie_id: int
) -> MovieModel:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        ).where(MovieModel.id == movie_id)
    )

    movie = result.unique().scalars().first()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def get_movies(
        request: Request,
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count(MovieModel.id))
    )
    total_items = count_result.scalar_one()
    total_pages = math.ceil(total_items / per_page) if total_items else 0

    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    prev_page = (
        f"/theater/movies/?page={page-1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page+1}&per_page={per_page}"
        if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )



@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if existing.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    try:
        country = await get_or_create_country(db, movie_data.country)
        genres = await _get_or_create_genres(db, movie_data.genres)
        actors = await _get_or_create_actors(db, movie_data.actors)
        languages = await _get_or_create_languages(db, movie_data.languages)
        movie = MovieModel(
            name=movie_data.name,
            date=movie_data.date,
            score=movie_data.score,
            overview=movie_data.overview,
            status=movie_data.status,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        db.add(movie)
        await db.commit()
        await db.refresh(movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Invalid input data.")
        )

    movie = await _get_movie_or_404(db, movie.id)
    return movie

@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    movie = await _get_movie_or_404(db, movie_id)
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    await db.delete(movie)
    await db.commit()
    return None

@router.patch(
    "/movies/{movie_id}/",
    response_model=MessageResponseSchema,
)
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    update_fields = movie_data.model_dump(exclude_unset=True)

    try:
        for field, value in update_fields.items():
            setattr(movie, field, value)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        )
    return MessageResponseSchema(detail="Movie updated successfully.")
