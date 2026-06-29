from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    if not total_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")
    total_pages = ceil(total_items / per_page)
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    prev_page = None
    next_page = None

    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def get_or_create_country(
        db: AsyncSession,
        code: str
) -> CountryModel:
    result = await db.execute(select(CountryModel).where(CountryModel.code == code))
    country = result.scalars().first()
    if country:
        return country

    country = CountryModel(code=code)
    db.add(country)
    await db.flush()
    return country


async def get_or_create_by_name(
        db: AsyncSession,
        model,
        name: str
):
    result = await db.execute(select(model).where(model.name == name))
    instance = result.scalars().first()

    if instance:
        return instance

    instance = model(name=name)
    db.add(instance)
    await db.flush()
    return instance


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie_detail(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        ).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

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
async def create_movies(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    existing_movie = await db.execute(
        select(MovieModel)
        .where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        )
    )
    if existing_movie.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' "
                   f"and release date '{movie_data.date}' already exists."
        )

    country = await get_or_create_country(db, movie_data.country)
    genres = [
        await get_or_create_by_name(db, GenreModel, genre)
        for genre in movie_data.genres
    ]
    actors = [
        await get_or_create_by_name(db, ActorModel, actor)
        for actor in movie_data.actors
    ]
    languages = [
        await get_or_create_by_name(db, LanguageModel, language)
        for language in movie_data.languages
    ]
    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        overview=movie_data.overview,
        score=movie_data.score,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_data.name}' "
            f"and release date '{movie_data.date}' already exists."
        )
    await db.refresh(movie, attribute_names=[
        "country",
        "genres",
        "actors",
        "languages",
    ])
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel)
                              .where(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    updated_data = movie_data.model_dump(exclude_unset=True)

    for key, value in updated_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data."
        )

    return {"detail": "Movie updated successfully."}
