from math import ceil
from typing import Annotated
from iso3166 import countries as iso

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload


from database import get_db, MovieModel

from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieDetailSchema,
    MovieListItemSchema,
    MovieListResponseSchema,
    MoviePostRequestSchema,
    MoviePostResponseSchema,
    MovieUpdateSchema,
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


@router.post("/movies/", response_model=MoviePostResponseSchema)
async def add_movie(
    movie_data: MoviePostRequestSchema,  # це об'єкт, який автоматично буде створено з JSON-запиту, використовуючи Pydantic-схему MoviePostRequestSchema.
    db: AsyncSession = Depends(get_db),
):
    payload = (
        movie_data.model_dump()
    )  # Перетвори Pydantic-об'єкт movie_data у словник (dict).

    # Checking ISO 3166-1 alpha-3 country code and storing country name and code
    try:
        country = iso.get(payload["country"])
        if country.alpha3 != payload["country"]:
            raise KeyError
        payload["country"] = {"code": country.alpha3, "name": country.name}
    except KeyError:
        raise ValueError(
            f"{payload['country']} is not a valid ISO 3166-1 alpha-3 country code"
        )

    # pull data from database
    result = await db.execute(select(CountryModel.name))
    country_db = set(result.scalars())
    result = await db.execute(select(GenreModel.name))
    genres_db = set(result.scalars())
    result = await db.execute(select(ActorModel.name))
    actors_db = set(result.scalars())
    result = await db.execute(select(LanguageModel.name))
    languages_db = set(result.scalars())

    # Check if item in payload exists in items db, if not create it

    if payload["country"]["name"] not in country_db:
        country = await create_country(
            db=db,
            country=CountryCreateSchema(**payload["country"]),
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
        select(CountryModel).where(
            CountryModel.name == payload["country"]["name"]
        )
    )
    payload["country"] = country.scalar_one_or_none()

    print("start creating movie")
    new_movie = MovieModel(**payload)
    print(new_movie)
    db.add(new_movie)
    await db.commit()
    return new_movie


#
# @router.get("/movies/{movie_id}", response_model=MovieDetailSchema)
# async def get_movie_detail(
#     db: AsyncSession = Depends(get_db),
#     movie_id: int = Path(
#         ge=1,
#     ),
# ):
#     query = (
#         select(MovieModel)
#         .where(MovieModel.id == movie_id)
#         .options(
#             selectinload(MovieModel.actors),
#             selectinload(MovieModel.genres),
#             selectinload(MovieModel.languages),
#             joinedload(MovieModel.country),
#         )
#     )
#
#     result = await db.execute(query)
#     movie = result.scalar_one_or_none()
#     if not movie:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found."
#         )
#     return MovieDetailSchema.from_attributes(movie)
#
#
# @router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_movie(
#     db: AsyncSession = Depends(get_db),
#     movie_id: int = Path(
#         ge=1,
#     ),
# ):
#     query = select(MovieModel).where(MovieModel.id == movie_id)
#
#     result = await db.execute(query)
#     movie = result.scalar_one_or_none()
#     if not movie:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Movie with the given ID was not found.",
#         )
#     await db.delete(movie)
#     await db.commit()
#
#
# @router.put("/movies/{movie_id}", status_code=status.HTTP_200_OK)
# async def update_movie(
#     movie_update_data: MovieUpdateSchema,
#     db: AsyncSession = Depends(get_db),
#     movie_id: int = Path(
#         ge=1,
#     ),
# ):
#     movie = await get_movie(db, movie_id)
#
#     if not movie:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found."
#         )
#     for attr in movie_update_data.keys():
#         setattr(movie, attr, movie_update_data[attr])
#     await db.update(movie)
#     await db.commit()
#     await db.refresh(movie)
#
#     return MovieDetailSchema.from_attributes(movie)
