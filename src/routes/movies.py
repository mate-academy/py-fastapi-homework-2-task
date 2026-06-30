import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MovieStatusEnum,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateRequest,
    MovieUpdateRequest,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items_query = select(func.count(MovieModel.id))
    total_items_result = await db.execute(total_items_query)
    total_items = total_items_result.scalar() or 0

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    offset = (page - 1) * per_page

    movies_query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )

    movies_result = await db.execute(movies_query)
    movies = movies_result.scalars().all()

    return {
        "movies": movies,
        "prev_page": (
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        "next_page": (
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    payload: MovieCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    duplicate_query = select(MovieModel).where(
        MovieModel.name == payload.name,
        MovieModel.date == payload.date,
    )
    duplicate_result = await db.execute(duplicate_query)

    if duplicate_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{payload.name}' "
                f"and release date '{payload.date}' already exists."
            ),
        )

    country_query = select(CountryModel).where(
        CountryModel.code == payload.country
    )
    country_result = await db.execute(country_query)
    country = country_result.scalars().first()

    if not country:
        country = CountryModel(code=payload.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for name in payload.genres:
        res = await db.execute(
            select(GenreModel).where(GenreModel.name == name)
        )
        genre = res.scalars().first()

        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)

        genres.append(genre)

    actors = []
    for name in payload.actors:
        res = await db.execute(
            select(ActorModel).where(ActorModel.name == name)
        )
        actor = res.scalars().first()

        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)

        actors.append(actor)

    languages = []
    for name in payload.languages:
        res = await db.execute(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        language = res.scalars().first()

        if not language:
            language = LanguageModel(name=name)
            db.add(language)

        languages.append(language)

    await db.flush()

    movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=MovieStatusEnum(payload.status),
        budget=payload.budget,
        revenue=payload.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()

    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    result = await db.execute(stmt)
    return result.scalars().first()


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie_details(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )

    result = await db.execute(query)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete(
    "/{movie_id}/",
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

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()
    return None


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    payload: MovieUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return {"detail": "Movie updated successfully."}

    for key, value in update_data.items():
        if key == "status" and value is not None:
            value = MovieStatusEnum(value)
        setattr(movie, key, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )

    return {"detail": "Movie updated successfully."}
