from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
import math
from src.database import get_db
from src.database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from src.schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieDetailSchema,
    MoviesListResponse,
    MovieShort,
)

router = APIRouter(tags=["Movies"])


def _get_movie_full_load_stmt(movie_id: int | None = None):
    stmt = select(MovieModel).options(
        joinedload(MovieModel.country),
        joinedload(MovieModel.genres),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.languages),
    )
    if movie_id is not None:
        stmt = stmt.where(MovieModel.id_ == movie_id)
    return stmt.distinct()


@router.get("/movies/", response_model=MoviesListResponse)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    count_stmt = select(func.count()).select_from(MovieModel)
    total_items = await db.scalar(count_stmt) or 0

    if total_items == 0:
        return MoviesListResponse(
            movies=[],
            total_items=0,
            total_pages=0,
            prev_page=None,
            next_page=None,
        )

    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(
            status_code=404, detail="Page number exceeds maximum available pages."
        )

    offset = (page - 1) * per_page

    stmt = (
        select(MovieModel).order_by(desc(MovieModel.id_)).offset(offset).limit(per_page)
    )
    result = await db.execute(stmt)
    movies = result.scalars().all()

    base_path_for_links = "/theater/movies"
    prev_page_path = (
        f"{base_path_for_links}/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page_path = (
        f"{base_path_for_links}/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return MoviesListResponse(
        movies=[MovieShort.model_validate(movie) for movie in movies],
        total_items=total_items,
        total_pages=total_pages,
        prev_page=prev_page_path,
        next_page=next_page_path,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = _get_movie_full_load_stmt(movie_id=movie_id)
    result = await db.execute(stmt)

    movie = result.scalars().unique().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return MovieDetailSchema.model_validate(movie)


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(movie_data: MovieCreate, db: AsyncSession = Depends(get_db)):
    existing_stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name, MovieModel.date == movie_data.release_date
    )
    if await db.scalar(existing_stmt):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' and release date "
                f"'{movie_data.release_date}' already exists."
            ),
        )

    async def get_or_create_related_models(
        session: AsyncSession, model, names_or_name: str | list[str]
    ):
        if not names_or_name:
            return None if not isinstance(names_or_name, list) else []

        names_list = (
            [names_or_name] if not isinstance(names_or_name, list) else names_or_name
        )

        results = []
        for name in names_list:
            name = name.strip()
            if not name:
                continue

            search_field = model.code if model is CountryModel else model.name

            stmt = select(model).where(search_field == name)
            instance = await session.scalar(stmt)

            if not instance:
                if model is CountryModel:
                    instance = model(code=name)
                else:
                    instance = model(name=name)
                session.add(instance)
            results.append(instance)

        return results[0] if not isinstance(names_or_name, list) else results

    new_movie = MovieModel(
        name=movie_data.name,
        date=movie_data.release_date,
        overview=movie_data.overview,
        score=movie_data.score,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=await get_or_create_related_models(
            db, CountryModel, movie_data.country
        ),
        genres=await get_or_create_related_models(db, GenreModel, movie_data.genres),
        actors=await get_or_create_related_models(db, ActorModel, movie_data.actors),
        languages=await get_or_create_related_models(
            db, LanguageModel, movie_data.languages
        ),
    )

    db.add(new_movie)
    await db.commit()

    stmt_full = _get_movie_full_load_stmt(movie_id=new_movie.id_)
    result = await db.execute(stmt_full)
    movie_with_details = result.scalars().first()

    return MovieDetailSchema.model_validate(movie_with_details)


@router.patch("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(
    movie_id: int, movie_data: MovieUpdate, db: AsyncSession = Depends(get_db)
):
    stmt = _get_movie_full_load_stmt(movie_id=movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for key, value in movie_data.model_dump(exclude_unset=True).items():
        if key == "release_date":
            setattr(movie, "date", value)
        elif key not in ["country", "genres", "actors", "languages"]:
            setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

    return MovieDetailSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id_ == movie_id)
    movie = await db.scalar(stmt)

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return None
