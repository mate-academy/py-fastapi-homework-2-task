from fastapi import APIRouter, Depends, HTTPException, Query, , status
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
    MovieUpdateSchema
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
            detail="No movies found for the specified page."
        )

    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    # Виконуємо запит на отримання фільмів з пагінацією
    result = await db.execute(
        select(MovieModel).offset((page - 1) * per_page).limit(per_page).order_by(MovieModel.id)
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


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=201)
async def create_film(
    movie: MovieCreateResponseSchema,
    db: AsyncSession = Depends(get_db),
):
    # Перевірка на дублікат
    result = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    # Країна
    country = None
    if movie.country_id:
        country = await db.get(CountryModel, movie.country_id)
    elif movie.country_name:
        result = await db.execute(select(CountryModel).where(CountryModel.name == movie.country_name))
        country = result.scalar_one_or_none()
        if not country:
            country = CountryModel(name=movie.country_name)
            db.add(country)
            await db.flush()

    if not country:
        raise HTTPException(status_code=400, detail="Country information is missing or invalid")

    # Жанри
    genres = []
    if movie.genre_ids:
        genres = (await db.execute(select(GenreModel).where(GenreModel.id.in_(movie.genre_ids)))).scalars().all()
    for name in movie.genre_names:
        genre = (await db.execute(select(GenreModel).where(GenreModel.name == name))).scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # Актори
    actors = []
    if movie.actor_ids:
        actors = (await db.execute(select(ActorModel).where(ActorModel.id.in_(movie.actor_ids)))).scalars().all()
    for name in movie.actor_names:
        actor = (await db.execute(select(ActorModel).where(ActorModel.name == name))).scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # Мови
    languages = []
    if movie.language_ids:
        languages = (
            await db.execute(select(LanguageModel).where(
                LanguageModel.id.in_(movie.language_ids)))).scalars().all()
    for name in movie.language_names:
        language = (await db.execute(select(LanguageModel).where(
            LanguageModel.name == name))).scalar_one_or_none()
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    # Створення фільму
    db_movie = MovieModel(
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

    db.add(db_movie)
    await db.commit()
    await db.refresh(db_movie)

    # Повертаємо фільм з повними зв’язками
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == db_movie.id)
    )
    movie_with_relations = result.scalar_one()

    return movie_with_relations


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

    return movie


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
    # Отримуємо фільм
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    # Валідуємо вручну числові поля (оскільки вони optional)
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

    # Оновлюємо лише надані поля
    data_to_update = movie_data.dict(exclude_unset=True)
    for field, value in data_to_update.items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
