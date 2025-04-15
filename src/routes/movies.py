from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailListSchema,
    MovieCreateResponseSchema,
    MovieDetailResponseSchema,
    MovieUpdateSchema, MovieCreateRequestSchema
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_all_films(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    # Отримуємо загальну кількість фільмів
    result = await db.execute(select(MovieModel))
    total_items = len(result.all())

    if total_items == 0:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Виконуємо запит на отримання фільмів з пагінацією
    result = await db.execute(
        select(MovieModel).offset((page - 1) * per_page).limit(per_page).order_by(MovieModel.id.desc())
    )
    movies = result.scalars().all()

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListResponseSchema(
        movies=[MovieDetailListSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", status_code=201, response_model=MovieCreateResponseSchema)
async def create_movie(movie_data: MovieCreateRequestSchema, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date
        )
    )
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # Get or create country by code
    country = await db.scalar(select(CountryModel).where(CountryModel.code == movie_data.country))
    if not country:
        country = CountryModel(code=movie_data.country, name=movie_data.country)
        db.add(country)
        await db.flush()

    # Get or create genres
    genres = []
    for name in movie_data.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == name))
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # Get or create actors
    actors = []
    for name in movie_data.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == name))
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # Get or create languages
    languages = []
    for name in movie_data.languages:
        language = await db.scalar(select(LanguageModel).where(LanguageModel.name == name))
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    # Create the movie
    movie = MovieModel(
        name=movie_data.name,
        date=movie_data.date,
        score=movie_data.score,
        overview=movie_data.overview,
        status=movie_data.status,
        budget=movie_data.budget,
        revenue=movie_data.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie.id)
    )
    movie = result.scalar_one()
    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailResponseSchema.model_validate(movie)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    # Шукаємо фільм у БД
    movie = await db.get(MovieModel, movie_id)

    # Якщо не знайдено — повертаємо 404
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    # Видаляємо фільм
    await db.delete(movie)
    await db.commit()

    # 204 — No Content, нічого не повертаємо
    return


@router.patch("/movies/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    if movie_data.score is not None and not (0 <= movie_data.score <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data. Score must be between 0 and 100."
        )
    if movie_data.budget is not None and movie_data.budget < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data. Budget must be non-negative."
        )
    if movie_data.revenue is not None and movie_data.revenue < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data. Revenue must be non-negative."
        )

    data_to_update = movie_data.model_dump(exclude_unset=True)
    for field, value in data_to_update.items():
        setattr(movie, field, value)
    await db.commit()
    await db.refresh(movie)
    return {"detail": "Movie updated successfully."}
