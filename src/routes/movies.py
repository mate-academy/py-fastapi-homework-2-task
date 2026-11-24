import math

from typing import Annotated

from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieDetailSchema, MovieListResponseSchema, MovieUpdateSchema


router = APIRouter()


async def get_or_create(model, data: list[str], db: AsyncSession):
    obj_list = []

    for obj in data:
        stmt = select(model).where(model.name == obj)
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            db_obj = model(
                name=obj
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        obj_list.append(db_obj)

    return obj_list


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movie_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    count_items = await db.execute(
        select(func.count()).select_from(MovieModel)
    )
    total_items = count_items.scalar() or 0
    total_pages = math.ceil(total_items / per_page)

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )
    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    start_item = per_page * page - per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(start_item)
        .limit(per_page)
    )
    movies = result.scalars().all()

    full_url = router.url_path_for("get_movie_list")
    prev_page = (
        f"/theater{full_url}?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"/theater{full_url}?page={page + 1}&per_page={per_page}"
        if (total_pages - page) >= 1
        else None
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_items=total_items,
        total_pages=total_pages,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )

    result = await db.execute(stmt)
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie: dict,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        movie_data = MovieCreateSchema.model_validate(movie)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )

    stmt_movie = select(MovieModel).where(
        MovieModel.name == movie_data.name, MovieModel.date == movie_data.date,
    )

    result = await db.execute(stmt_movie)
    db_movie = result.scalar_one_or_none()
    if db_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and "
                f"release date '{movie_data.date}' already exists."
            )
        )

    stmt_country = select(CountryModel).where(CountryModel.code == movie_data.country)
    result = await db.execute(stmt_country)
    db_country = result.scalar_one_or_none()
    if db_country is None:
        db_country = CountryModel(
            code=movie_data.country
        )
        db.add(db_country)
        await db.commit()
        await db.refresh(db_country)

    genres_list = await get_or_create(GenreModel, movie_data.genres, db)
    actors_list = await get_or_create(ActorModel, movie_data.actors, db)
    languages_list = await get_or_create(LanguageModel, movie_data.languages, db)

    db_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=db_country,
        genres=genres_list,
        actors=actors_list,
        languages=languages_list,
    )
    db.add(db_movie)
    await db.commit()

    return db_movie


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_id: int,
    movie_data: dict,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        update_data = MovieUpdateSchema.model_validate(
            movie_data
        ).model_dump(exclude_unset=True)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )

    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    for key, value in update_data.items():
        setattr(db_movie, key, value)

    await db.commit()

    return JSONResponse({"detail": "Movie updated successfully."})


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(db_movie)
    await db.commit()
