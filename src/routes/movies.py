from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
import schemas


router = APIRouter()


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

    movie_list = [schemas.MovieListItemSchema(**movie.__dict__) for movie in movies]

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if len(movies) == per_page else None

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page

    return schemas.MovieListResponseSchema(
        movies=movie_list,
        prev_page=prev_page,
        next_page=next_page,
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

    if len(movie.name) > 255:
        raise HTTPException(status_code=400, detail="Movie name exceeds maximum length of 255 characters.")

    if movie.date.year > date.today().year + 1:
        raise HTTPException(status_code=400, detail="Movie date cannot be in the future.")

    if movie.score < 0 or movie.score > 100:
        raise HTTPException(status_code=400, detail="Movie score must be between 0 and 100.")

    if movie.budget < 0 or movie.revenue < 0:
        raise HTTPException(status_code=400, detail="Movie budget and revenue cannot be negative.")

    country_result = await db.scalars(select(CountryModel).where(CountryModel.code == movie.country))
    country = country_result.first()
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.commit()

    genres = []
    for genre_name in movie.genres:
        genre_result = await db.scalars(select(GenreModel).where(GenreModel.name == genre_name))
        genre = genre_result.first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
            await db.commit()
            await db.refresh(genre)

        genres.append(genre)

    actors = []
    for actor_name in movie.actors:
        actor_result = await db.scalars(select(ActorModel).where(ActorModel.name == actor_name))
        actor = actor_result.first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
            await db.commit()
            await db.refresh(actor)

        actors.append(actor)

    languages = []
    for language_name in movie.languages:
        language_result = await db.scalars(select(LanguageModel).where(LanguageModel.name == language_name))
        language = language_result.first()
        if not language:
            language = LanguageModel(name=language_name)
            db.add(language)
            await db.commit()
            await db.refresh(language)

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
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))

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
    if movie_update.score is not None and (movie_update.score > 100 or movie_update.score < 0):
        raise HTTPException(status_code=400, detail="Movie score must be between 0 and 100.")

    if movie_update.budget is not None and movie_update.budget < 0:
        raise HTTPException(status_code=400, detail="Movie budget cannot be negative.")

    if movie_update.revenue is not None and movie_update.revenue < 0:
        raise HTTPException(status_code=400, detail="Movie revenue cannot be negative.")

    result = await db.scalars(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    update_data = movie_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))

    return {"detail": "Movie updated successfully."}
