from math import ceil
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status
)
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas import MovieListResponseSchema, MovieDetailSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema

router = APIRouter()

ASession = Annotated[AsyncSession, Depends(get_db)]


async def _get_movie(session: AsyncSession, movie_id: int):
    return await session.scalar(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .execution_options(populate_existing=True)
    )


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def get_all_movies(
        session: ASession,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
):
    total_items = await session.scalar(
        select(func.count(MovieModel.id))
    )
    total_pages = ceil(total_items / per_page)

    movies = (await session.scalars(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )).all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    def link(p: int) -> str:
        return f"/theater/movies/?page={p}&per_page={per_page}"
    return {
        "movies": movies,
        "prev_page": link(page - 1) if page > 1 else None,
        "next_page": link(page + 1) if page < total_pages else None,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
        session: ASession,
        movie: MovieCreateSchema,
):
    if await session.scalar(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    ):
        raise HTTPException(
            status_code=409,
            detail="A movie with the name "
                   f"'{movie.name}' and release date "
                   f"'{movie.date}' already exists."
        )
    country = await session.scalar(
        select(CountryModel)
        .where(CountryModel.code == movie.country)
    )
    if not country:
        country = CountryModel(code=movie.country)
        session.add(country)
    genres = []
    for genre_name in movie.genres:
        genre = await session.scalar(
            select(GenreModel)
            .where(GenreModel.name == genre_name)
        )
        if not genre:
            genre = GenreModel(name=genre_name)
            session.add(genre)
        genres.append(genre)
    actors = []
    for actor_name in movie.actors:
        actor = await session.scalar(
            select(ActorModel)
            .where(ActorModel.name == actor_name)
        )
        if not actor:
            actor = ActorModel(name=actor_name)
            session.add(actor)
        actors.append(actor)
    languages = []
    for lan_name in movie.languages:
        lan = await session.scalar(
            select(LanguageModel)
            .where(LanguageModel.name == lan_name)
        )
        if not lan:
            lan = LanguageModel(name=lan_name)
            session.add(lan)
        languages.append(lan)
    db_movie = MovieModel(
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
    try:
        session.add(db_movie)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )
    return await _get_movie(session, db_movie.id)


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie(
        session: ASession,
        movie_id: int,
):
    movie = await _get_movie(session, movie_id)
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
        session: ASession,
        movie_id: int,
):
    db_movie = await session.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if not db_movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    await session.delete(db_movie)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/movies/{movie_id}/",
    status_code=status.HTTP_200_OK
)
async def update_movie(
        session: ASession,
        movie_id: int,
        movie: MovieUpdateSchema
):
    db_movie = await session.scalar(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    if db_movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    update_data = movie.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_movie, field, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid input data."
        )
    return {"detail": "Movie updated successfully."}
