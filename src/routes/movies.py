import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import (MovieListItemSchema,
                            MovieCreateSchema,
                            MovieUpdateSchema)

router = APIRouter()


def get_pagination_params(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    return {"page": page, "per_page": per_page}


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_films(
        db: AsyncSession = Depends(get_db),
        pagination: dict = Depends(get_pagination_params),
):
    page = pagination["page"]
    per_page = pagination["per_page"]

    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar()

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    start = (page - 1) * per_page

    result = await db.execute(
        select(
            MovieModel.id,
            MovieModel.name,
            MovieModel.date,
            MovieModel.score,
            MovieModel.overview,
        )
        .order_by(MovieModel.id.desc())
        .offset(start).limit(per_page)
    )
    movies = result.all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    movie_list = [
        MovieListItemSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview
        ) for movie in movies
    ]

    count_result = await db.execute(select(func.count(MovieModel.id)))
    total_items = count_result.scalar()
    total_pages = math.ceil(total_items / per_page)

    base_url = "/theater/movies/"
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" \
        if page > 1 else None
    next_page = f"{base_url}?page={page+1}&per_page={per_page}" \
        if page < total_pages else None

    return {
        "movies": movie_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
            selectinload(MovieModel.country),
        ).where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    country_obj = await db.scalar(
        select(CountryModel).where(CountryModel.code == movie.country)
    )
    if not country_obj:
        country_obj = CountryModel(code=movie.country)
        db.add(country_obj)

    genre_objs = []
    for genre_name in movie.genres:
        obj = await db.scalar(
            select(GenreModel).where(GenreModel.name == genre_name)
        )
        if not obj:
            obj = GenreModel(name=genre_name)
            db.add(obj)

        genre_objs.append(obj)

    actor_objs = []
    for actor_name in movie.actors:
        obj = await db.scalar(
            select(ActorModel).where(ActorModel.name == actor_name)
        )
        if not obj:
            obj = ActorModel(name=actor_name)
            db.add(obj)

        actor_objs.append(obj)

    language_objs = []
    for language_name in movie.languages:
        obj = await db.scalar(
            select(LanguageModel).where(LanguageModel.name == language_name)
        )
        if not obj:
            obj = LanguageModel(name=language_name)
            db.add(obj)

        language_objs.append(obj)

    await db.flush()

    new_film = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country_obj,
        genres=genre_objs,
        actors=actor_objs,
        languages=language_objs
    )

    try:
        db.add(new_film)
        await db.commit()
        result = await db.execute(
            select(MovieModel)
            .options(
                selectinload(MovieModel.country),
                selectinload(MovieModel.genres),
                selectinload(MovieModel.actors),
                selectinload(MovieModel.languages),
            )
            .where(MovieModel.id == new_film.id)
        )
        movie_with_relations = result.scalar_one()
        return movie_with_relations

    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_film(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(db_movie)
    await db.commit()

    return


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
        movie_id: int,
        movie: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    db_movie = result.scalar_one_or_none()

    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)

    try:
        await db.commit()
        await db.refresh(db_movie)
        return {"detail": "Movie updated successfully."}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
