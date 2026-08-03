import schemas
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel, models
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

router = APIRouter()


@router.get("/movies/", response_model=schemas.MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
) -> schemas.MovieListResponseSchema:

    total_items = await db.scalar(
        select(func.count(MovieModel.id)).select_from(MovieModel)
    )
    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    db_movies = await db.scalars(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
        .order_by(MovieModel.id.desc())
    )
    movies = db_movies.all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return schemas.MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/", response_model=schemas.MovieDetailSchema, status_code=201
)
async def create_movie(
    movie: schemas.MovieCreateSchema, db: AsyncSession = Depends(get_db)
) -> MovieModel:
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name, MovieModel.date == movie.date
        )
    )
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    country = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    if not country:
        country = CountryModel(code=movie.country)

    genres = []

    for genre in movie.genres:
        db_genre = await db.scalar(
            select(GenreModel).where(GenreModel.name == genre)
        )
        if not db_genre:
            genres.append(GenreModel(name=genre))
        else:
            genres.append(db_genre)

    actors = []
    for actor in movie.actors:
        db_actor = await db.scalar(
            select(ActorModel).where(ActorModel.name == actor)
        )
        if not db_actor:
            actors.append(ActorModel(name=actor))
        else:
            actors.append(db_actor)

    languages = []
    for language in movie.languages:
        db_language = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == language)
        )
        if not db_language:
            languages.append(LanguageModel(name=language))
        else:
            languages.append(db_language)

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
        languages=languages,
    )

    db.add(new_movie)
    try:
        await db.commit()
        await db.refresh(
            new_movie,
            attribute_names=["country", "genres", "actors", "languages"],
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )
    return new_movie


@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    db_movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    return schemas.MovieDetailSchema.model_validate(db_movie)


@router.delete(
    "/movies/{movie_id}/",
    status_code=204,
)
async def delete_movie_detail(
    movie_id: int, db: AsyncSession = Depends(get_db)
):
    db_movie = await db.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    await db.delete(db_movie)
    await db.commit()
    return


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie_detail(
    movie_id: int,
    movie_update: schemas.MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    db_movie = await db.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_movie, field, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
