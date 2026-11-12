import math
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from database.models import (
    MovieModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)
from services.movie_helpers import get_or_create_country, get_or_create_entities

router = APIRouter(prefix="/movies", tags=["Movies"])


async def check_movie_duplicate(db: AsyncSession, name: str, date) -> None:
    dup_stmt = select(MovieModel).where(
        MovieModel.name == name,
        MovieModel.date == date
    )
    existing = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{name}' and release date '{date}' already exists."
        )


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    count_query = select(func.count()).select_from(MovieModel)
    total_items = (await db.execute(count_query)).scalar_one()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    total_pages = math.ceil(total_items / per_page)
    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    offset = (page - 1) * per_page
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = (await db.execute(stmt)).scalars().all()

    base_path = "/theater/movies/"
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", response_model=MovieDetailResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailResponseSchema:
    await check_movie_duplicate(db, movie_data.name, movie_data.date)

    country = await get_or_create_country(db, movie_data.country)
    genres = await get_or_create_entities(db, GenreModel, movie_data.genres)
    actors = await get_or_create_entities(db, ActorModel, movie_data.actors)
    languages = await get_or_create_entities(db, LanguageModel, movie_data.languages)

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
    db.add(new_movie)
    await db.commit()

    await db.refresh(
        new_movie,
        attribute_names=["country", "genres", "actors", "languages"]
    )
    return new_movie


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailResponseSchema:
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> None:
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    if "name" in update_data or "date" in update_data:
        check_name = update_data.get("name", movie.name)
        check_date = update_data.get("date", movie.date)

        dup_stmt = select(MovieModel).where(
            MovieModel.name == check_name,
            MovieModel.date == check_date,
            MovieModel.id != movie_id
        )
        if (await db.execute(dup_stmt)).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A movie with the name '{check_name}' and release date '{check_date}' already exists."
            )

    if "country" in update_data:
        country_code = update_data.pop("country")
        country = await get_or_create_country(db, country_code)
        movie.country_id = country.id

    if "genres" in update_data:
        genres_names = update_data.pop("genres")
        movie.genres = await get_or_create_entities(db, GenreModel, genres_names)

    if "actors" in update_data:
        actors_names = update_data.pop("actors")
        movie.actors = await get_or_create_entities(db, ActorModel, actors_names)

    if "languages" in update_data:
        languages_names = update_data.pop("languages")
        movie.languages = await get_or_create_entities(db, LanguageModel, languages_names)

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
