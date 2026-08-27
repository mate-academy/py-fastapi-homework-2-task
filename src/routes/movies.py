from typing import TypeVar

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from dependencies import DB, PaginationDep
from schemas.movies import (
    MoviesPageSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies")

ModelType = TypeVar("ModelType")


async def get_or_create_country(db: DB, country_code: str):
    db_country = await db.scalar(
        select(CountryModel).where(CountryModel.code == country_code.upper())
    )

    if db_country is None:
        db_country = CountryModel(code=country_code.upper())
        db.add(db_country)
        await db.flush()

    return db_country


async def get_or_create_entities(
    db: DB,
    names: list[str],
    model: type[ModelType],
) -> list[ModelType]:
    entities = []

    for name in names:
        entity = await db.scalar(select(model).where(model.name == name))

        if entity is None:
            entity = model(name=name)
            db.add(entity)
            await db.flush()

        entities.append(entity)

    return entities


def validate_movie_data(movie: MovieCreateSchema) -> None:
    errors = []

    if not movie.name or len(movie.name) > 255:
        errors.append("name")
    if movie.budget < 0:
        errors.append("budget")
    if movie.revenue < 0:
        errors.append("revenue")
    if not movie.genres:
        errors.append("genres")
    if not movie.actors:
        errors.append("actors")
    if not movie.languages:
        errors.append("languages")

    if errors:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )


async def get_movie_by_id_or_404(
    db: DB,
    movie_id: int,
    load_relations: bool = False,
) -> MovieModel:
    movie = select(MovieModel).where(MovieModel.id == movie_id)

    if load_relations:
        movie = movie.options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )

    movie_db = await db.scalar(movie)

    if not movie_db:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return movie_db


@router.get(
    path="/",
    response_model=MoviesPageSchema,
    responses={
        200: {"description": "Successfully retrieved a paginated list of movies."},
        404: {"description": "No movies found for the specified page."},
    },
)
async def get_movies(request: Request, db: DB, pagination: PaginationDep):
    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = pagination.total_pages(total_items)

    db_movies = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    movies = db_movies.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return MoviesPageSchema(
        movies=movies,
        prev_page=(
            pagination.build_page_url("/theater/movies/", pagination.page - 1)
            if pagination.page > 1
            else None
        ),
        next_page=(
            pagination.build_page_url("/theater/movies/", pagination.page + 1)
            if pagination.page < total_pages
            else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    path="/{movie_id}/",
    response_model=MovieDetailSchema,
    status_code=200,
    responses={
        200: {"description": "Successfully retrieved the movie details."},
        404: {"description": "The movie with the specified ID does not exist."},
    },
)
async def get_movie(movie_id: int, db: DB):
    return await get_movie_by_id_or_404(movie_id=movie_id, db=db, load_relations=True)


@router.post(
    path="/",
    response_model=MovieDetailSchema,
    status_code=201,
    responses={
        201: {
            "description": "The movie was successfully created, "
            "and its details are returned in the response."
        },
        400: {
            "description": "The input data is invalid "
            "(e.g., missing required fields, invalid values)."
        },
        409: {"description": "Invalid input data."},
    },
)
async def create_movie(movie: MovieCreateSchema, db: DB):
    validate_movie_data(movie)

    db_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date,
        )
    )

    if db_movie is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{db_movie.name}' "
            f"and release date '{db_movie.date}' already exists.",
        )

    country = await get_or_create_country(db, movie.country)
    genres = await get_or_create_entities(db=db, model=GenreModel, names=movie.genres)
    actors = await get_or_create_entities(db=db, model=ActorModel, names=movie.actors)
    languages = await get_or_create_entities(
        db=db, model=LanguageModel, names=movie.languages
    )

    movie_model = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie_model)
    await db.commit()

    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_model.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    return result.scalar_one()


@router.delete(
    path="/{movie_id}/",
    status_code=204,
    responses={
        204: {"description": "The movie was successfully deleted."},
        404: {"description": "The movie with the specified ID does not exist."},
    },
)
async def delete_movie(movie_id: int, db: DB):
    db_movie = await get_movie_by_id_or_404(movie_id=movie_id, db=db)

    await db.delete(db_movie)
    await db.commit()


@router.patch(
    path="/{movie_id}/",
    status_code=200,
    responses={
        200: {"description": "Movie updated successfully."},
        400: {"description": "Invalid input data."},
        404: {"description": "Movie with the given ID was not found."},
    },
)
async def update_movie(
    movie_id: int,
    movie_updates: MovieUpdateSchema,
    db: DB,
):
    db_movie = await get_movie_by_id_or_404(movie_id=movie_id, db=db)

    update_data = movie_updates.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()
    await db.refresh(db_movie)

    return {"detail": "Movie updated successfully."}
