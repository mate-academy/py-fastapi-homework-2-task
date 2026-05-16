from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from iso3166 import countries_by_alpha3

from database import get_db, MovieModel
from database.models import (
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from schemas.movies import (
    CountryDetailSchema,
    ActorDetailSchema,
    LanguageDetailSchema,
    GenreDetailSchema,
    MovieRetrieveSchema,
    MovieDetailSchema,
    MovieListItemSchema,
    MovieCreateSchema,
    MovieUpdateSchema
)


async def get_movie_or_404(db: AsyncSession, movie_id: int) -> MovieModel:
    result = await db.execute(
        select(MovieModel).options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.languages),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.country),
        ).where(MovieModel.id == movie_id)
    )
    movie = result.unique().scalar_one_or_none()

    if not movie:
        raise HTTPException(
            detail="Movie with the given ID was not found.",
            status_code=404,
        )

    return movie


router = APIRouter()


@router.get("/movies/", response_model=MovieListItemSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
) -> dict:
    count_result = await db.execute(
        select(func.count(MovieModel.id))
    )
    count_movies = count_result.first()[0]
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .offset(offset)
        .limit(per_page)
        .order_by(MovieModel.id.desc()),
    )
    movie_list = result.scalars().all()
    movies_per_page = len(movie_list)
    total_pages = (count_movies + per_page - 1) // per_page
    if not movies_per_page:
        raise HTTPException(
            detail="No movies found.",
            status_code=404
        )

    return MovieListItemSchema(
        movies=[
            MovieRetrieveSchema(
                id=movie.id,
                name=movie.name,
                overview=movie.overview,
                date=movie.date,
                score=movie.score
            )
            for movie in movie_list
        ],
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        total_pages=total_pages,
        total_items=count_movies
    ).model_dump()


@router.post(
    "/movies/",
    response_model=MovieDetailSchema,
    status_code=201
)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> MovieModel:
    async def _get_or_create_items(
        model_type: type[GenreModel | ActorModel | LanguageModel],
        field_values: list[str],
    ) -> list:
        result = await db.execute(
            select(model_type).where(model_type.name.in_(field_values))
        )
        item_list = list(result.scalars().all())

        for value in field_values:
            item = model_type(name=value)

            if item not in item_list:
                item_list.append(item)
                db.add(item)

        await db.commit()
        return item_list

    query = select(MovieModel).options(
        joinedload(MovieModel.genres),
        joinedload(MovieModel.languages),
        joinedload(MovieModel.actors),
        joinedload(MovieModel.country),
    ).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    )
    result = await db.execute(query)
    movie = result.unique().scalar_one_or_none()

    if movie:
        raise HTTPException(
            detail=(
                f"A movie with the name '{movie.name}'"
                f" and release date '{movie.date.strftime('%Y-%m-%d')}' "
                "already exists."
            ),
            status_code=409,
        )

    country = CountryModel(
        code=movie_data.country,
        name=countries_by_alpha3.get(movie_data.country)
    )
    genres = await _get_or_create_items(GenreModel, movie_data.genres)
    actors = await _get_or_create_items(ActorModel, movie_data.actors)
    languages = await _get_or_create_items(
        LanguageModel,
        movie_data.languages
    )
    movie_dict_data = {
        key: value
        for key, value in movie_data.model_dump().items()
        if key not in ("country", "genres", "actors", "languages")
    }
    movie = MovieModel(
        **movie_dict_data,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )
    db.add(country)
    db.add_all(genres)
    db.add_all(actors)
    db.add_all(languages)
    await db.commit()
    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=CountryDetailSchema(
            id=movie.country.id,
            code=movie.country.code,
            name=movie.country.name,
        ),
        languages=[
            LanguageDetailSchema(
                id=language.id,
                name=language.name,
            )
            for language in movie.languages
        ],
        actors=[
            ActorDetailSchema(
                id=actor.id,
                name=actor.name,
            )
            for actor in movie.actors
        ],
        genres=[
            GenreDetailSchema(
                id=genre.id,
                name=genre.name,
            )
            for genre in movie.genres
        ],
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailSchema,
)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> MovieModel:
    movie = await get_movie_or_404(db, movie_id)
    return MovieDetailSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=CountryDetailSchema(
            id=movie.country.id,
            code=movie.country.code,
            name=movie.country.name,
        ),
        languages=[
            LanguageDetailSchema(
                id=language.id,
                name=language.name,
            )
            for language in movie.languages
        ],
        actors=[
            ActorDetailSchema(
                id=actor.id,
                name=actor.name,
            )
            for actor in movie.actors
        ],
        genres=[
            GenreDetailSchema(
                id=genre.id,
                name=genre.name,
            )
            for genre in movie.genres
        ],
    )


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    movie = await get_movie_or_404(db, movie_id)
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def partial_update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> dict:
    await get_movie_or_404(db, movie_id)
    await db.execute(
        update(MovieModel).where(MovieModel.id == movie_id).values(
            {
                key: value
                for key, value in movie_data.model_dump().items()
                if value is not None
            }
        )
    )
    await db.commit()
    return {"detail": "Movie updated successfully."}
