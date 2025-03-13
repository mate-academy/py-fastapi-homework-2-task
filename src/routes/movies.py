from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.session_postgresql import get_postgresql_db as get_db
from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateRequestSchema,
    MovieUpdateRequestSchema
)

router = APIRouter()


def get_pagination_params(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
):
    return {"page": page, "per_page": per_page}


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_list_movies(
    pagination: dict = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db)
):
    page = pagination["page"]
    per_page = pagination["per_page"]

    query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .order_by(desc(MovieModel.id))
    )
    total_items_query = select(func.count(MovieModel.id))

    offset_val = (page - 1) * per_page
    movies_result = await db.execute(query.offset(offset_val).limit(per_page))
    movies = movies_result.unique().scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_items = (await db.execute(total_items_query)).scalar() or 0
    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/movies"
    prev_page = f"{base_url}/?page={page-1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_url}/?page={page+1}&per_page={per_page}" if page < total_pages else None

    movie_list = [MovieListItemSchema.from_orm(movie) for movie in movies]

    return {
        "movies": movie_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_in: MovieCreateRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    if len(movie_in.name) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must not exceed 255 characters."
        )
    one_year_from_now = date.today() + timedelta(days=365)
    if movie_in.date > one_year_from_now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie date must not be more than one year in the future."
        )
    if not (0 <= movie_in.score <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score must be between 0 and 100."
        )
    if movie_in.budget < 0 or movie_in.revenue < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget/Revenue must be non-negative."
        )

    duplicate_query = select(MovieModel).where(
        MovieModel.name == movie_in.name,
        MovieModel.date == movie_in.date
    )
    existing_movie = (await db.execute(duplicate_query)).scalar_one_or_none()
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie_in.name}' and release date '{movie_in.date}' already exists."
        )

    country = None
    if movie_in.country:
        query_country = select(CountryModel).where(CountryModel.code == movie_in.country)
        country = (await db.execute(query_country)).scalar_one_or_none()
        if not country:
            country = CountryModel(code=movie_in.country)
            db.add(country)
            await db.flush()

    genres_list = []
    for g in movie_in.genres or []:
        query_genre = select(GenreModel).where(GenreModel.name.ilike(g))
        genre_obj = (await db.execute(query_genre)).scalar_one_or_none()
        if not genre_obj:
            genre_obj = GenreModel(name=g)
            db.add(genre_obj)
            await db.flush()
        genres_list.append(genre_obj)

    actors_list = []
    for a in movie_in.actors or []:
        query_actor = select(ActorModel).where(ActorModel.name.ilike(a))
        actor_obj = (await db.execute(query_actor)).scalar_one_or_none()
        if not actor_obj:
            actor_obj = ActorModel(name=a)
            db.add(actor_obj)
            await db.flush()
        actors_list.append(actor_obj)

    languages_list = []
    for lang in movie_in.languages or []:
        query_lang = select(LanguageModel).where(LanguageModel.name.ilike(lang))
        lang_obj = (await db.execute(query_lang)).scalar_one_or_none()
        if not lang_obj:
            lang_obj = LanguageModel(name=lang)
            db.add(lang_obj)
            await db.flush()
        languages_list.append(lang_obj)

    new_movie = MovieModel(
        name=movie_in.name,
        date=movie_in.date,
        score=movie_in.score,
        overview=movie_in.overview,
        status=movie_in.status,
        budget=movie_in.budget,
        revenue=movie_in.revenue,
        country=country,
        genres=genres_list,
        actors=actors_list,
        languages=languages_list
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return new_movie


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie_result = await db.execute(query)
    movie = movie_result.unique().scalars().one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await db.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int, data: MovieUpdateRequestSchema, db: AsyncSession = Depends(get_db)):
    query = select(MovieModel).where(MovieModel.id == movie_id)
    movie = (await db.execute(query)).scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    if data.name is not None:
        if len(data.name) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data."
            )
        movie.name = data.name

    if data.date is not None:
        one_year_from_now = date.today() + timedelta(days=365)
        if data.date > one_year_from_now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data."
            )
        movie.date = data.date

    if data.score is not None:
        if not (0 <= data.score <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data."
            )
        movie.score = data.score

    if data.overview is not None:
        movie.overview = data.overview

    if data.status is not None:
        movie.status = data.status

    if data.budget is not None:
        if data.budget < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data."
            )
        movie.budget = data.budget

    if data.revenue is not None:
        if data.revenue < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input data."
            )
        movie.revenue = data.revenue

    await db.commit()
    return {"detail": "Movie updated successfully."}
