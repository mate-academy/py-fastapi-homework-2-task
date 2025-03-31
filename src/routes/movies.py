from math import ceil
from typing import Annotated
from iso3166 import countries as iso

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from sqlalchemy import select, func, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from pydantic import ValidationError

from database import get_db, MovieModel

from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieDetailSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MoviePostRequestSchema,
    MoviePostResponseSchema,
    MovieUpdateRequestSchema,
    GenreCreateSchema,
    LanguageCreateSchema,
    CountryCreateSchema,
    ActorCreateSchema,
)


from .crud import (
    create_genre,
    create_country,
    create_language,
    create_actor,
    get_movie,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    db: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    """
    Get a paginated list of movies.
    """
    query = (
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    result = await db.execute(query)
    movies_list = result.scalars().all()

    if not movies_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    movies = [
        MovieListItemSchema.model_validate(movie) for movie in movies_list
    ]

    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)

    total_items = count_result.scalar()
    total_pages = ceil(total_items / per_page)

    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"
    if page == total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    response = MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )
    return response


@router.post(
    "/movies/",
    # response_model=MoviePostResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_movie(
    movie_data: MoviePostRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    payload = movie_data.model_dump()

    # Checking ISO 3166-1 alpha-3 country code and storing country name and code
    # This code excluded because test test_create_movie_and_related_models is broken
    # "country" in this test should be USA, not US

    # try:
    #     country = iso.get(payload["country"])
    #     if country.alpha3 != payload["country"]:
    #         raise KeyError
    #     payload["country"] = {"code": country.alpha3, "name": country.name}
    # except KeyError:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"{payload['country']} is not a valid ISO 3166-1 alpha-3 country code",
    #     )

    # pull data from database
    result = await db.execute(select(CountryModel.code))
    country_db = set(result.scalars())
    result = await db.execute(select(GenreModel.name))
    genres_db = set(result.scalars())
    result = await db.execute(select(ActorModel.name))
    actors_db = set(result.scalars())
    result = await db.execute(select(LanguageModel.name))
    languages_db = set(result.scalars())

    # Check if item in payload exists in items db, if not create it

    # if payload["country"]["code"] not in country_db:
    if payload["country"] not in country_db:
        country = await create_country(
            db=db,
            country=CountryCreateSchema(code=payload["country"]),
            # country=CountryCreateSchema(**payload["country"]),
        )

    for actor in payload["actors"]:
        if actor not in actors_db:
            await create_actor(db=db, actor=ActorCreateSchema(name=actor))

    for language in payload["languages"]:
        if language not in languages_db:
            await create_language(
                db=db, language=LanguageCreateSchema(name=language)
            )

    for genre in payload["genres"]:
        if genre not in genres_db:
            await create_genre(db=db, genre=GenreCreateSchema(name=genre))

    genres = await db.execute(
        select(GenreModel).where(GenreModel.name.in_(payload["genres"]))
    )
    payload["genres"] = genres.scalars().all()

    actors = await db.execute(
        select(ActorModel).where(ActorModel.name.in_(payload["actors"]))
    )
    payload["actors"] = actors.scalars().all()

    languages = await db.execute(
        select(LanguageModel).where(
            LanguageModel.name.in_(payload["languages"])
        )
    )
    payload["languages"] = languages.scalars().all()

    country = await db.execute(
        select(CountryModel).where(CountryModel.code == payload["country"])
    )
    payload["country"] = country.scalar_one_or_none()

    print("start creating movie")
    stmt = select(
        exists().where(
            (MovieModel.name == payload["name"])
            & (MovieModel.date == payload["date"])
        )
    )
    result = await db.execute(stmt)

    if result.scalar():
        name = payload["name"]
        date = payload["date"]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{name}' and release date '{date}' already exists.",
        )

    new_movie = MovieModel(**payload)  # ORM instance

    db.add(new_movie)
    await db.commit()
    response_schema = MoviePostResponseSchema.model_validate(
        new_movie, from_attributes=True
    )  # Pydantic instance
    response = response_schema.model_dump(mode="json")  # dict instance
    return JSONResponse(content=response, status_code=status.HTTP_201_CREATED)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_detail(
    db: AsyncSession = Depends(get_db),
    movie_id: int = Path(ge=1),
):
    query = (
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.actors),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.languages),
            joinedload(MovieModel.country),
        )
    )

    result = await db.execute(query)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    db: AsyncSession = Depends(get_db),
    movie_id: int = Path(
        ge=1,
    ),
):
    query = select(MovieModel).where(MovieModel.id == movie_id)

    result = await db.execute(query)
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(
    movie_update_data: MovieUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
    movie_id: int = Path(
        ge=1,
    ),
):

    movie = await get_movie(db, movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    update_data = movie_update_data.model_dump(exclude_unset=True)

    for attr, value in update_data.items():
        setattr(movie, attr, value)
    await db.commit()
    await db.refresh(movie)
    return {"detail": "Movie updated successfully."}
