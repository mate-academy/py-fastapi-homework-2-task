from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieListResponseSchema, MovieDetailSchema, MovieCreateSchema, MovieUpdateSchema

router = APIRouter(prefix="/movies", tags=["movies"])


async def get_or_create_related_entity(
        db: AsyncSession,
        model,
        field_name: str,
        value: str,
):
    field = getattr(model, field_name)
    entity = await db.scalar(select(model).where(field == value))

    if entity is None:
        entity = model(**{field_name: value})
        db.add(entity)

    return entity


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
        db: Annotated[AsyncSession, Depends(get_db)],
        request: Request,
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=20),
) -> dict:
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_items = total_items or 0
    total_pages = (total_items + per_page - 1) // per_page

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    base_url = request.url.path.removeprefix(
        request.app.state.api_version_prefix
    )

    return {
        "movies": movies,
        "prev_page": (
            f"{base_url}?page={page - 1}&per_page={per_page}"
            if page > 1
            else None
        ),
        "next_page": (
            f"{base_url}?page={page + 1}&per_page={per_page}"
            if page < total_pages
            else None
        ),
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/",
    response_model=MovieDetailSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieModel:
    existing_movie = await db.scalar(
        select(MovieModel).where(
            MovieModel.name == movie_data.name,
            MovieModel.date == movie_data.date,
            )
    )

    if existing_movie is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        )

    country = await get_or_create_related_entity(
        db,
        CountryModel,
        "code",
        movie_data.country,
    )
    genres = [
        await get_or_create_related_entity(db, GenreModel, "name", name)
        for name in dict.fromkeys(movie_data.genres)
    ]
    actors = [
        await get_or_create_related_entity(db, ActorModel, "name", name)
        for name in dict.fromkeys(movie_data.actors)
    ]
    languages = [
        await get_or_create_related_entity(db, LanguageModel, "name", name)
        for name in dict.fromkeys(movie_data.languages)
    ]

    movie_values = movie_data.model_dump(
        exclude={"country", "genres", "actors", "languages"}
    )
    movie = MovieModel(
        **movie_values,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    try:
        db.add(movie)
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with the name '{movie_data.name}' "
                f"and release date '{movie_data.date}' already exists."
            ),
        ) from error

    return movie


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema
)
async def get_movie_by_id(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieModel:
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )

    movie = result.unique().scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    return movie


@router.delete(
    "/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{movie_id}/")
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    movie = await db.get(MovieModel, movie_id)

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data.",
        ) from error

    return {"detail": "Movie updated successfully."}
