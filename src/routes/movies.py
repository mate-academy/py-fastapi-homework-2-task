from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieCreateRequestSchema, MovieDetailSchema
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page

    result = await db.execute(select(MovieModel).limit(per_page).offset(offset).order_by(MovieModel.id.desc()))
    movies = result.scalars().all()

    total_items_query = await db.execute(select(func.count(MovieModel.id)))
    total_items = total_items_query.scalar()
    total_pages = (total_items + per_page - 1) // per_page

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    if not movies or (page > total_pages):
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .filter(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.post("/movies/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        existing_movie = await db.execute(
            select(MovieModel).filter(
                MovieModel.name == movie_data.name,
                MovieModel.date == movie_data.date,
            )
        )
        if existing_movie.scalars().first():
            raise HTTPException(
                status_code=409,
                detail=f"A movie with the name '{movie_data.name}' and release date "
                       f"'{movie_data.date}' already exists."
            )
        country = await db.execute(
            select(CountryModel).filter(CountryModel.code == movie_data.country)
        )
        country = country.scalars().first()
        if not country:
            country = CountryModel(code=movie_data.country)
            db.add(country)

        genres = []
        for genre_name in movie_data.genres:
            genre = await db.execute(
                select(GenreModel).filter(GenreModel.name == genre_name)
            )
            genre = genre.scalars().first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
            genres.append(genre)

        actors = []
        for actor_name in movie_data.actors:
            actor = await db.execute(
                select(ActorModel).filter(ActorModel.name == actor_name)
            )
            actor = actor.scalars().first()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
            actors.append(actor)

        languages = []
        for language_name in movie_data.languages:
            language = await db.execute(
                select(LanguageModel).filter(LanguageModel.name == language_name)
            )
            language = language.scalars().first()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
            languages.append(language)

        new_movie = MovieModel(
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
        db.add(new_movie)

        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to create movie due to integrity error. Please check the data."
        )
    return new_movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).filter(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()
    return


@router.patch("/movies/{movie_id}/", status_code=200, response_model=dict)
async def update_movie(
    movie_id: int,
    updates: dict,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel).filter(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    if "score" in updates:
        if not (0 <= updates["score"] <= 100):
            raise HTTPException(status_code=400, detail="Invalid input data. Score must be between 0 and 100.")

    if "budget" in updates and updates["budget"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data. Budget must be non-negative.")

    if "revenue" in updates and updates["revenue"] < 0:
        raise HTTPException(status_code=400, detail="Invalid input data. Revenue must be non-negative.")

    for key, value in updates.items():
        if hasattr(movie, key):
            setattr(movie, key, value)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid field: '{key}' is not a valid attribute.")

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}
