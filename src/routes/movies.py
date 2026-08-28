from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


router = APIRouter()

RelatedModel = TypeVar(
    "RelatedModel",
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)

MOVIE_NOT_FOUND = "Movie with the given ID was not found."


async def _get_or_create(
    db: AsyncSession,
    model: type[RelatedModel],
    field_name: str,
    value: str,
) -> RelatedModel:
    field = getattr(model, field_name)
    result = await db.execute(select(model).where(field == value))
    instance = result.scalar_one_or_none()

    if instance is None:
        instance = model(**{field_name: value})
        db.add(instance)
        await db.flush()

    return instance


async def _get_movie_with_relations(
    db: AsyncSession,
    movie_id: int,
) -> MovieModel | None:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    return result.unique().scalar_one_or_none()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    total_items = await db.scalar(select(func.count(MovieModel.id))) or 0
    total_pages = (total_items + per_page - 1) // per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = list(result.scalars().all())

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_url = "/theater/movies/"
    prev_page = (
        f"{base_url}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
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
) -> MovieModel:
    duplicate = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        )

    try:
        country = await _get_or_create(
            db, CountryModel, "code", movie_data.country
        )
        genres = [
            await _get_or_create(db, GenreModel, "name", name)
            for name in movie_data.genres
        ]
        actors = [
            await _get_or_create(db, ActorModel, "name", name)
            for name in movie_data.actors
        ]
        languages = [
            await _get_or_create(db, LanguageModel, "name", name)
            for name in movie_data.languages
        ]

        movie = MovieModel(
            **movie_data.model_dump(
                exclude={"country", "genres", "actors", "languages"}
            ),
            country=country,
            genres=genres,
            actors=actors,
            languages=languages,
        )
        db.add(movie)
        await db.commit()
        return movie
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.date}' already exists."
            ),
        ) from error


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieModel:
    movie = await _get_movie_with_relations(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND)
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND)

    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail=MOVIE_NOT_FOUND)

    update_values = movie_data.model_dump(exclude_unset=True)
    if any(value is None for value in update_values.values()):
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for field_name, value in update_values.items():
        setattr(movie, field_name, value)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.") from error

    return {"detail": "Movie updated successfully."}
