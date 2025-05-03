from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import datetime

from starlette import status

from schemas.movies import MovieUpdate
from src.database import get_db, MovieModel
from src.database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from src.schemas.movies import MoviesList, MovieCreate, MovieDetail, MovieShort

router = APIRouter()


@router.get("/movies/", response_model=MoviesList)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items_result = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_result.scalar()

    total_pages = (total_items + per_page - 1) // per_page

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )
    movies_list = [MovieShort.from_orm(movie) for movie in movies]
    return MoviesList(
        movies=movies_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/", response_model=MovieDetail, status_code=status.HTTP_201_CREATED
)
async def create_movie(film: MovieCreate, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(
        MovieModel.name == film.name, MovieModel.date == film.date
    )
    result = await db.execute(query)
    existing_movie = result.scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{film.name}' and release date '{film.date}' already exists.",
        )
    today = datetime.date.today()
    one_year_later = today + datetime.timedelta(days=365)
    if film.date > one_year_later:
        raise HTTPException(
            status_code=400, detail="Date cannot be more than a year in the future."
        )

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == film.country)
    )
    if not country:
        country = CountryModel(code=film.country)
        db.add(country)
        await db.flush()

    genres = []
    for name in film.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == name))
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in film.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == name))
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in film.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == name)
        )
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    movie = MovieModel(
        name=film.name,
        date=film.date,
        score=film.score,
        overview=film.overview,
        status=film.status,
        budget=film.budget,
        revenue=film.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(movie)
    await db.commit()
    await db.refresh(
        movie, attribute_names=["country", "genres", "actors", "languages"]
    )

    return movie


@router.get("/movies/{movie_id}/", response_model=MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )

    movie = movie.scalar()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()

    return {"message": "Movie successfully deleted."}


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    data_movie: MovieUpdate, movie_id: int, db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    for key, value in data_movie.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    db.add(movie)
    await db.commit()

    return {"detail": "Movie updated successfully."}
