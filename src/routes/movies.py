from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel, MovieStatusEnum
import schemas


router = APIRouter()
INVALID_INPUT_DETAIL = "Invalid input data."
VALID_MOVIE_STATUSES = {movie_status.value for movie_status in MovieStatusEnum}


def raise_invalid_input():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_INPUT_DETAIL)


def is_valid_country_code(country: str) -> bool:
    return country.isalpha() and len(country) in {2, 3}


def validate_movie_data(movie: schemas.MovieCreate | schemas.MovieUpdate):
    if movie.name is not None and len(movie.name) > 255:
        raise_invalid_input()

    if movie.date is not None and movie.date > date.today() + timedelta(days=365):
        raise_invalid_input()

    if movie.score is not None and (movie.score < 0 or movie.score > 100):
        raise_invalid_input()

    if movie.budget is not None and movie.budget < 0:
        raise_invalid_input()

    if movie.revenue is not None and movie.revenue < 0:
        raise_invalid_input()

    if movie.status is not None and movie.status not in VALID_MOVIE_STATUSES:
        raise_invalid_input()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
):
    skip = (page - 1) * per_page
    result = await db.scalars(
        select(MovieModel).offset(skip).limit(per_page).order_by(desc(MovieModel.id))
    )
    movies = result.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page

    return schemas.MovieListResponseSchema(
        movies=movies,
        prev_page=f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None,
        next_page=f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=schemas.MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: schemas.MovieCreate, db: AsyncSession = Depends(get_db)):
    existing_movie_result = await db.scalars(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    if existing_movie_result.first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    validate_movie_data(movie)
    if not is_valid_country_code(movie.country):
        raise_invalid_input()

    country_result = await db.scalars(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_result.first()
    try:
        if not country:
            country = CountryModel(code=movie.country)
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie.genres:
            genre_result = await db.scalars(select(GenreModel).where(GenreModel.name == genre_name))
            genre = genre_result.first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()

            genres.append(genre)

        actors = []
        for actor_name in movie.actors:
            actor_result = await db.scalars(select(ActorModel).where(ActorModel.name == actor_name))
            actor = actor_result.first()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()

            actors.append(actor)

        languages = []
        for language_name in movie.languages:
            language_result = await db.scalars(select(LanguageModel).where(LanguageModel.name == language_name))
            language = language_result.first()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()

            languages.append(language)

        new_movie = MovieModel(
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
            languages=languages
        )

        db.add(new_movie)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise_invalid_input()

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == new_movie.id)
    )
    return result.unique().scalars().first()


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.scalars(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
        .where(MovieModel.id == movie_id)
    )
    movie = result.first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.scalars(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie_update: schemas.MovieUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.scalars(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    validate_movie_data(movie_update)
    update_data = movie_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise_invalid_input()

    return {"detail": "Movie updated successfully."}
