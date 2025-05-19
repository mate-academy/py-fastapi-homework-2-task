import math

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieBaseSchema, MovieCreateSchema, MovieUpdateSchema, \
    MovieDetailSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema, status_code=200)
async def get_movies(
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    offset = (page - 1) * per_page
    result = await db.execute(select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page))
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = (await db.execute(func.count(MovieModel.id))).scalar()
    total_pages = math.ceil(total_items / per_page)
    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    )

    return MovieListResponseSchema(
        movies=[MovieBaseSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and"
                   f" release date '{movie.date}' already exists."
        )

    try:
        result = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
        country = result.scalar_one_or_none()
        if not country:
            country = CountryModel(code=movie.country, name="")
            db.add(country)
            await db.flush()

        genres = []
        for genre_name in movie.genres:
            result = await db.execute(select(GenreModel).where(GenreModel.name == genre_name))
            genre = result.scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        actors = []
        for actor_name in movie.actors:
            result = await db.execute(select(ActorModel).where(ActorModel.name == actor_name))
            actor = result.scalar_one_or_none()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            actors.append(actor)

        languages = []
        for language_name in movie.languages:
            result = await db.execute(select(LanguageModel).where(LanguageModel.name == language_name))
            language = result.scalar_one_or_none()
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
            actors=actors,
            genres=genres,
            languages=languages,
            country=country,
        )
        db.add(new_movie)
        await db.commit()
        await db.refresh(
            new_movie,
            ["genres", "actors", "languages", "country"]
        )
        return MovieDetailSchema.model_validate(new_movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data")


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema, status_code=200)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages)
        )
    )
    result = await db.execute(query)
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return MovieDetailSchema.model_validate(movie, from_attributes=True)


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()

    return Response(status_code=204, headers=None)


@router.patch("/movies/{movie_id}/", status_code=200)
async def update_movie(movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(query)
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    for key, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
