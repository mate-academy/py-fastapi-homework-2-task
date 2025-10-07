import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieCreateSchema, MovieListItemSchema, MovieDetailSchema, \
    MovieUpdateSchema

router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListItemSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {
                "application/json": {
                    "example": {"detail": "No movies found."},
                },
            },
        },
    },
)
async def get_movies(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
) -> MovieListItemSchema:

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = math.ceil(total_items / per_page)

    if not total_items or page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    movies = (await db.scalars(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )).all()

    return MovieListItemSchema(
        movies=movies,
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        total_pages=total_pages,
        total_items=total_items,
    )


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "content": {"application/json": {"example": {"detail": "Invalid input data."}}},
        },
        status.HTTP_409_CONFLICT: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": "A movie with that name and release date already exists."
                    }
                }
            },
        },
    },
)
async def create_movie(
    movie: MovieCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):

    movie_in_db = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    if movie_in_db:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    country = await db.scalar(select(CountryModel).where(CountryModel.code == movie.country))
    if not country:
        country = CountryModel(code=movie.country)
        db.add(country)
        await db.flush()

    genres = []
    for el in movie.genres:
        genre = await db.scalar(select(GenreModel).where(GenreModel.name == el))
        if not genre:
            genre = GenreModel(name=el)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for el in movie.actors:
        actor = await db.scalar(select(ActorModel).where(ActorModel.name == el))
        if not actor:
            actor = ActorModel(name=el)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for el in movie.languages:
        language = await db.scalar(select(LanguageModel).where(LanguageModel.name == el))
        if not language:
            language = LanguageModel(name=el)
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
        languages=languages,
    )
    db.add(new_movie)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )
    await db.refresh(new_movie, attribute_names=["country", "genres", "actors", "languages"])
    return new_movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given ID was not found."},
                },
            },
        },
    },
)
async def get_movie(movie_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    movie = await db.get(
        MovieModel,
        movie_id,
        options=[
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        ]
    )
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Movie with the given ID was not found."}}}
        }
    },
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return None


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Movie with the given ID was not found."}}}},
        status.HTTP_400_BAD_REQUEST: {
            "content": {"application/json": {"example": {"detail": "Invalid input data."}}}},
    },
)
async def update_movie(
    movie_id: int,
    payload: MovieUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    print(update_data)

    try:
        if "score" in update_data and not (0 <= update_data["score"] <= 100):
            raise ValueError()
        if "budget" in update_data and update_data["budget"] < 0:
            raise ValueError()
        if "revenue" in update_data and update_data["revenue"] < 0:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input data.")

    for field, value in update_data.items():
        setattr(movie, field, value)

    db.add(movie)
    await db.commit()
    return {"detail": "Movie updated successfully."}
