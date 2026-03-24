from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieDetailSchema, MovieListItemSchema, MovieUpdateSchema, MovieCreateSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListItemSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page

    offset = (page - 1) * per_page
    result = await db.execute(select(MovieModel).order_by(
        *MovieModel.default_order_by()).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return MovieListItemSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
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

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()
    return


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
    )

    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    data = data.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
        data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    existing = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == data.name,
            MovieModel.date == data.date
        )
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{data.name}' and release date '{data.date}' already exists."
        )

    country = await db.scalar(
        select(CountryModel).where(
            CountryModel.code == data.country
        )
    )
    if not country:
        country = CountryModel(code=data.country)
        db.add(country)
        await db.flush()

    genres = []
    for item in data.genres:
        genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == item)
        )
        if not genre:
            genre = GenreModel(name=item)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for item in data.actors:
        actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == item)
        )
        if not actor:
            actor = ActorModel(name=item)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for item in data.languages:
        language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == item)
        )
        if not language:
            language = LanguageModel(name=item)
            db.add(language)
            await db.flush()
        languages.append(language)

    movie = MovieModel(
        name=data.name,
        date=data.date,
        score=data.score,
        overview=data.overview,
        status=data.status,
        budget=data.budget,
        revenue=data.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(movie)
    await db.commit()

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
    movie = result.unique().scalar_one()
    return movie
