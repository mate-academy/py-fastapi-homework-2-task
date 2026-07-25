import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import movies


router = APIRouter()


@router.get("/movies/", response_model=movies.MovieListResponseSchema)
async def get_all_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
) -> movies.MovieListResponseSchema:
    total_items_result = await db.execute(
        select(func.count(MovieModel.id))
    )
    total_items = total_items_result.scalar_one()
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page

    if not total_items or page > total_pages:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    movies_result = await db.execute(
        select(MovieModel)
        .options(joinedload(MovieModel.country))
        .options(joinedload(MovieModel.actors))
        .options(joinedload(MovieModel.genres))
        .options(joinedload(MovieModel.languages))
        .order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies_items = list(movies_result.unique().scalars().all())

    return movies.MovieListResponseSchema(
        movies=movies_items,
        prev_page=(
            f"/theater/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        next_page=(
            f"/theater/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        total_items=total_items,
        total_pages=total_pages
    )


@router.post(
    "/movies/",
    response_model=movies.MovieDetailSchema,
    status_code=201
)
async def create_movie(
    data: movies.MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> MovieModel:
    async def _get_or_create_items(
        item_model: type,
        items_data: list[str],
        db_: AsyncSession
    ) -> list:
        items = []

        for item_data in items_data:
            try:
                item = item_model(name=item_data)
                db_.add(item)
                await db_.commit()
                await db_.refresh(item)
            except IntegrityError:
                item_result = await db_.execute(
                    select(item_model)
                    .where(item_model.name == item_data)
                )
                item = item_result.scalar_one()

            items.append(item)

        return items

    existing_movie_result = await db.execute(
        select(MovieModel)
        .options(joinedload(MovieModel.genres))
        .options(joinedload(MovieModel.country))
        .options(joinedload(MovieModel.languages))
        .options(joinedload(MovieModel.actors))
        .where(
            MovieModel.name == data.name,
            MovieModel.date == data.date
        )
    )
    existing_movie = existing_movie_result.unique().scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A movie with the name '{data.name}' "
                f"and release date '{data.date}' already exists."
            )
        )

    data = data.model_dump()
    country_data = data.pop("country")
    genres_data = data.pop("genres")
    actors_data = data.pop("actors")
    languages_data = data.pop("languages")

    movie = MovieModel(**data)

    try:
        country = CountryModel(code=country_data)
        db.add(country)
        await db.commit()
        await db.refresh(country)
    except IntegrityError:
        country_result = await db.execute(
            select(CountryModel)
            .where(CountryModel.name == country_data)
        )
        country = country_result.scalar_one()

    movie.country = country

    genres = await _get_or_create_items(
        GenreModel,
        genres_data,
        db
    )
    actors = await _get_or_create_items(
        ActorModel,
        actors_data,
        db
    )
    languages = await _get_or_create_items(
        LanguageModel,
        languages_data,
        db
    )

    movie.genres = genres
    movie.actors = actors
    movie.languages = languages

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return movies.MovieDetailSchema(
        id=movie.id,
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


@router.get("/movies/{movie_id}/", response_model=movies.MovieDetailSchema)
async def get_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> MovieModel:
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(joinedload(MovieModel.genres))
        .options(joinedload(MovieModel.actors))
        .options(joinedload(MovieModel.languages))
        .options(joinedload(MovieModel.country))
    )
    movie_item: MovieModel = result.unique().scalar_one_or_none()

    if not movie_item:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie_item


@router.patch("/movies/{movie_id}/")
async def update_movie_by_id(
    movie_id: int,
    data: movies.MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> dict:
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie: MovieModel = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    movie.name = data.name if data.name is not None else movie.name
    movie.date = data.date if data.date is not None else movie.date
    movie.score = data.score if data.score is not None else movie.score
    movie.overview = (
        data.overview
        if data.overview is not None
        else movie.overview
    )
    movie.status = data.status if data.status is not None else movie.status
    movie.budget = data.budget if data.budget is not None else movie.budget
    movie.revenue = data.revenue if data.revenue is not None else movie.revenue

    await db.commit()
    await db.refresh(movie)

    return {"detail": "Movie updated successfully."}


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie_by_id(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
    )
    movie_item = result.scalar_one_or_none()

    if not movie_item:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    await db.delete(movie_item)
    await db.commit()
