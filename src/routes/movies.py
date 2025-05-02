from http.client import HTTPResponse
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

router = APIRouter()

NO_MOVIES_ERROR = "No movies found."
NO_MOVIE_ID_ERROR = "Movie with the given ID was not found."
MOVIE_UPDATED = "Movie updated successfully."


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIES_ERROR}}
            },
        }
    },
)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1),
):
    total = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = ceil(total / per_page)

    if total == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail=NO_MOVIES_ERROR)

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    movies = result.scalars().all()

    url_ = "/theater/movies?page="
    next_page = (
        f"{url_}{page + 1}&per_page={per_page}" if page < total_pages else None
    )
    prev_page = f"{url_}{page - 1}&per_page={per_page}" if page > 1 else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total,
    )


async def _get_movie_by_id(db: AsyncSession, movie_id: int) -> MovieModel:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()
    if movie is None:
        raise HTTPException(status_code=404, detail=NO_MOVIE_ID_ERROR)
    return movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIE_ID_ERROR}}
            }
        }
    },
)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await _get_movie_by_id(db, movie_id)
    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid input data."},
        409: {"description": "Movie already exists"},
    },
)
async def create_movie(
    payload: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    exists = await db.scalar(
        select(func.count())
        .select_from(MovieModel)
        .where(
            MovieModel.name == payload.name,
            MovieModel.date == payload.date,
        )
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{payload.name}' "
                f"and release date '{payload.date}' already exists."
            ),
        )
    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == payload.country)
    )
    if not country:
        country = CountryModel(code=payload.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in payload.genres:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == name)
        )
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in payload.actors:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == name)
        )
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in payload.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()
    await db.refresh(
        movie, attribute_names=["country", "genres", "actors", "languages"]
    )

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await _get_movie_by_id(db, movie_id)
    await db.delete(movie)
    await db.commit()
    return None


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {"example": {"detail": MOVIE_UPDATED}}
            }
        },
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIES_ERROR}}
            }
        },
    },
)
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await _get_movie_by_id(db, movie_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(movie, field, value)
    await db.commit()
    return {"detail": MOVIE_UPDATED}
