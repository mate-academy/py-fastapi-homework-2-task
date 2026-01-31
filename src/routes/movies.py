from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from crud import get_or_create_entities
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieDetailSchema
from schemas.movies import MovieListResponseSchema, MovieListItemSchema, \
    MovieUpdateSchema, MovieCreateSchema

router = APIRouter()


async def get_movies_list(db: AsyncSession, offset, per_page):
    result = await db.execute(
        select(MovieModel).offset(offset).limit(per_page).order_by(
            MovieModel.id.desc()))
    return result.scalars().all()


@router.get("/movies/", description="get all movies 🎬️")
async def list_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
) -> MovieListResponseSchema:
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if total_items <= 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    movies = await get_movies_list(db=db, offset=offset, per_page=per_page)

    movies_schema = [
        MovieListItemSchema.model_validate(movie)
        for movie in movies
    ]

    text_prev = None
    text_next = None
    show_prev_page = page - 1 if page > 1 else None

    if show_prev_page:
        text_prev = f"/theater/movies/?page={show_prev_page}&per_page={per_page}"

    show_next_page = page + 1 if page <= total_pages else None

    if show_next_page:
        text_next = f"/theater/movies/?page={show_next_page}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=movies_schema,
        prev_page=text_prev,
        next_page=text_next,
        total_pages=total_pages,
        total_items=total_items
    )


async def get_movie_by_id(movie_id, db):
    stmt = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
    ).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar()
    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema,
            description="get one movie 🎥")
async def get_one_movies(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await get_movie_by_id(movie_id, db)

    if not result:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    return result


@router.delete("/movies/{movie_id}/", status_code=204,
               description="delete movie by id🎥")
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    movie_to_delete = await get_movie_by_id(movie_id, db)

    if not movie_to_delete:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    stmt = delete(MovieModel).where(MovieModel.id == movie_id)

    await db.execute(stmt)
    await db.commit()


@router.patch("/movies/{movie_id}/", description="update movie")
async def update_movie(
        movie_id: int,
        data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    movie_to_update = await get_movie_by_id(movie_id, db)

    if not movie_to_update:
        raise HTTPException(status_code=404,
                            detail="Movie with the given ID was not found.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie_to_update, field, value)

    try:
        db.add(movie_to_update)
        await db.commit()
        await db.refresh(movie_to_update)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return {"detail": "Movie updated successfully."}


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201
)
async def create_movie(
        db: Annotated[AsyncSession, Depends(get_db)],
        movie_data: MovieCreateSchema
):
    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        )
    )
    if existing_movie.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' "
                   f"and release date '{movie_data.date}' already exists."
        )

    country_query = await db.execute(
        select(CountryModel).where(CountryModel.code == movie_data.country)
    )
    db_country = country_query.scalar_one_or_none()

    if not db_country:
        db_country = CountryModel(code=movie_data.country, name=None)
        db.add(db_country)

    db_genres = await get_or_create_entities(
        db, GenreModel, movie_data.genres
    )
    db_actors = await get_or_create_entities(
        db, ActorModel, movie_data.actors
    )
    db_languages = await get_or_create_entities(
        db, LanguageModel, movie_data.languages
    )

    movie_fields = movie_data.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )

    db_movie = MovieModel(
        **movie_fields,
        country=db_country,
        genres=db_genres,
        actors=db_actors,
        languages=db_languages
    )

    db.add(db_movie)

    try:
        await db.commit()
        query = (
            select(MovieModel)
            .where(MovieModel.id == db_movie.id)
            .options(
                joinedload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages)
            )
        )
        result = await db.execute(query)
        db_movie = result.scalar_one()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return db_movie
