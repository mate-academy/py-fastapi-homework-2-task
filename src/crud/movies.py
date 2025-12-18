from typing import Dict
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from database.models import (
    Base,
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    MovieCreate,
    MovieDetailResponse,
    MovieUpdate
)


def generate_pagination_links(
    total_pages: int,
    page: int,
    per_page: int
) -> dict[str, str]:
    base_url = "/theater/movies/"
    prev_page = (
        f"{base_url}?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )
    return {
        "prev_page": prev_page,
        "next_page": next_page
    }


async def get_movie_list(
        db: AsyncSession,
        page: int,
        per_page: int
) -> list[MovieModel]:
    offset = (page - 1) * per_page
    query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    movies = result.scalars().all()
    return movies


async def get_or_create_entity(
        db: AsyncSession,
        model: Base,
        value: str
) -> Base:
    if model == CountryModel:
        field_value = {"code": value}
    else:
        field_value = {"name": value}

    result = await db.execute(select(model).filter_by(**field_value))
    db_model = result.scalars().first()
    if not db_model:
        db_model = model(**field_value)
        db.add(db_model)
        await db.flush()
    return db_model


async def create_movie(
        db: AsyncSession,
        movie: MovieCreate
) -> MovieDetailResponse:
    async with db.begin():
        result = await db.execute(
            select(MovieModel)
            .where(
                and_(
                    MovieModel.name == movie.name,
                    MovieModel.date == movie.date
                )
            )
        )
        db_movie = result.scalars().first()
        if db_movie:
            raise HTTPException(
                status_code=409,
                detail=(f"A movie with the name '{movie.name}' "
                        f"and release date '{movie.date}' already exists.")
            )
        country_obj = await get_or_create_entity(
            db=db,
            model=CountryModel,
            value=movie.country
        )
        genres_obj = [
            await get_or_create_entity(
                db=db,
                model=GenreModel,
                value=genre
            )
            for genre in movie.genres
        ]
        actors_obj = [
            await get_or_create_entity(
                db=db,
                model=ActorModel,
                value=actor
            )
            for actor in movie.actors
        ]
        languages_obj = [
            await get_or_create_entity(
                db=db,
                model=LanguageModel,
                value=language
            )
            for language in movie.languages
        ]
        movie_obj = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=country_obj,
            genres=genres_obj,
            actors=actors_obj,
            languages=languages_obj
        )
        db.add(movie_obj)
        await db.flush()
    query = select(MovieModel).options(
        joinedload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == movie_obj.id)
    result = await db.execute(query)
    created_movie = result.scalars().first()
    return MovieDetailResponse.model_validate(
        created_movie
    )


async def get_single_movie(
        db: AsyncSession,
        movie_id: int
) -> MovieDetailResponse:
    db_movie = select(MovieModel).options(
        joinedload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)
    result = await db.execute(db_movie)
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return MovieDetailResponse.model_validate(
        movie
    )


async def delete_movie(
        db: AsyncSession,
        movie_id: int
) -> None:
    db_movie = (await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
    )).scalar_one_or_none()
    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(db_movie)
    await db.commit()


async def update_movie(
        db: AsyncSession,
        movie_id: int,
        movie_update: MovieUpdate
) -> Dict[str, str]:
    db_movie = await db.get(MovieModel, movie_id)
    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    update_data = movie_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)
    await db.commit()
    await db.refresh(db_movie)
    return {
        "detail": "Movie updated successfully."
    }
