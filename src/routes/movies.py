from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import ValidationError

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieCreateSchema, MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    total_items = await db.scalar(select(func.count(MovieModel.id)))
    total_pages = (total_items + per_page - 1) // per_page

    result = await db.scalars(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = result.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = None
    if page > 1:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    next_page = None
    if page < total_pages:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    movie = result.unique().scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        movie_data: dict,  # приймаємо сирий dict, не схему
        db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    try:
        validated = MovieUpdateSchema(**movie_data)
    except ValidationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )

    update_data = validated.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201,
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
):
    # 1. перевірка дубліката
    existing = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    # 2. country: get-or-create за кодом
    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie_data.country)
    )
    if country is None:
        country = CountryModel(code=movie_data.country)
        db.add(country)
        await db.flush()

    # 3. genres: get-or-create для кожної назви
    genres = []
    for name in movie_data.genres:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == name)
        )
        if genre is None:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    # 4. actors
    actors = []
    for name in movie_data.actors:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == name)
        )
        if actor is None:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    # 5. languages
    languages = []
    for name in movie_data.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if language is None:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    # 6. створити фільм з об'єктами
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

    # 7. перезавантажити зі зв'язками для відповіді
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie.id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    return result.unique().scalar_one()
