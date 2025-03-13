from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
    MoviesGenresModel,
    ActorsMoviesModel,
    MoviesLanguagesModel
)
from schemas import MovieListResponseSchema
from schemas.movies import MovieCreateResponseSchema, MovieDetailResponseSchema, MovieUpdateRequestSchema, \
    UpdateResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page

    result = await db.execute(select(MovieModel).order_by(desc(MovieModel.id)).offset(offset).limit(per_page))

    movies = result.scalars().all()

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreateResponseSchema, db: AsyncSession = Depends(get_db)):
    max_date = date.today() + timedelta(days=365)
    if movie.date > max_date:
        raise HTTPException(
            status_code=400, detail="Date cannot be more than one year in the future."
        )

    existing_movie_query = select(MovieModel).filter(
        MovieModel.name == movie.name, MovieModel.date == movie.date
    )
    existing_movie_result = await db.execute(existing_movie_query)
    if existing_movie_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists.",
        )

    try:
        country_query = select(CountryModel).filter(CountryModel.code == movie.country)
        country_result = await db.execute(country_query)
        country = country_result.scalar_one_or_none()
        if not country:
            country = CountryModel(code=movie.country)
            db.add(country)
            await db.flush()

        new_movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country_id=country.id,
        )
        db.add(new_movie)
        await db.flush()

        for genre_name in movie.genres:
            genre_query = select(GenreModel).filter(GenreModel.name == genre_name)
            genre_result = await db.execute(genre_query)
            genre = genre_result.scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                await db.flush()
            await db.execute(
                MoviesGenresModel.insert().values(
                    movie_id=new_movie.id, genre_id=genre.id
                )
            )

        for actor_name in movie.actors:
            actor_query = select(ActorModel).filter(ActorModel.name == actor_name)
            actor_result = await db.execute(actor_query)
            actor = actor_result.scalar_one_or_none()
            if not actor:
                actor = ActorModel(name=actor_name)
                db.add(actor)
                await db.flush()
            await db.execute(
                ActorsMoviesModel.insert().values(
                    movie_id=new_movie.id, actor_id=actor.id
                )
            )

        for language_name in movie.languages:
            language_query = select(LanguageModel).filter(
                LanguageModel.name == language_name
            )
            language_result = await db.execute(language_query)
            language = language_result.scalar_one_or_none()
            if not language:
                language = LanguageModel(name=language_name)
                db.add(language)
                await db.flush()
            await db.execute(
                MoviesLanguagesModel.insert().values(
                    movie_id=new_movie.id, language_id=language.id
                )
            )

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating movie: {str(e)}")

    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    return MovieDetailResponseSchema.from_orm(result.scalar_one())


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        ).where(MovieModel.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return MovieDetailResponseSchema.from_orm(movie)


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))

    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(db_movie)
    await db.commit()
    return None


@router.patch("/movies/{movie_id}/", response_model=UpdateResponseSchema)
async def update_movie(
        movie_id: int,
        update_data: MovieUpdateRequestSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))

    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_dict = update_data.dict(exclude_unset=True)
    if "date" in update_dict and update_dict["date"] > datetime.date.today() + datetime.timedelta(days=365):
        raise HTTPException(
            status_code=400, detail="Date cannot be more than one year in the future."
        )

    for key, value in update_dict.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return {"detail": "Movie updated successfully."}
