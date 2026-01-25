import asyncio
import math

from fastapi import HTTPException
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from database.models import MovieModel, CountryModel, GenreModel, ActorModel, LanguageModel, Base
from schemas.movies import MovieInputCreateSchema, MovieUpdateSchema


def get_page_url(page: int, per_page: int) -> str:
    return f"/theater/movies/?page={page}&per_page={per_page}"


def get_http_exception_with_detail(status_code: int, exc_name: str, msg: str):
    return HTTPException(
        status_code=status_code,
        detail=[
            {
                "loc": ["query", exc_name],
                "msg": msg,
            }
        ],
    )


def get_http_exception_without_detail(status_code: int, msg: str):
    return HTTPException(status_code=status_code, detail=msg)


async def read_movies(db: AsyncSession, page: int, per_page: int):
    total_items_query = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items_query.scalar_one()

    if not 1 <= per_page <= 20:
        raise get_http_exception_with_detail(
            status_code=422,
            exc_name="Invalid per_page",
            msg="Input should be greater than or equal to 1"
        )

    total_pages = math.ceil(total_items / per_page)
    if not 1 <= page:
        raise get_http_exception_with_detail(
            status_code=422,
            exc_name="Invalid page",
            msg="Input should be greater than or equal to 1"
        )

    if not total_items:
        raise get_http_exception_without_detail(
            status_code=404,
            msg="No movies found."
        )

    prev_page = None
    if page > 1:
        prev_page = get_page_url(page=page - 1, per_page=per_page)

    next_page = None
    if page < total_pages:
        next_page = get_page_url(page=page + 1, per_page=per_page)

    stmt = (select(MovieModel)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .order_by(desc(MovieModel.id)))
    result = await db.execute(stmt)
    result_query = result.unique().scalars().all()
    if not result_query:
        raise HTTPException(status_code=404, detail="No movies found.")

    return {
        "movies": result_query,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


async def read_movie(movie_id: int, db: AsyncSession):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    result = result.scalar()
    if not result:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return result


async def create_model(db_model, params, db: AsyncSession):
    model_obj = db_model(**params)
    db.add(model_obj)
    await db.commit()
    return model_obj


async def create_movie(movie_schema: MovieInputCreateSchema, db: AsyncSession):
    async def get_coro_func(db_model, schema_attr):
        stmt = select(db_model).where(db_model.name == schema_attr)
        coro_obj = await db.execute(stmt)
        coro_obj = coro_obj.scalar()
        if not coro_obj:
            coro_obj = db_model(name=schema_attr)
            db.add(coro_obj)
        return coro_obj

    stmt_movie = (select(MovieModel)
                  .where(
        and_(
            MovieModel.name == movie_schema.name,
            MovieModel.date == movie_schema.date
        )
    ))
    result = await db.execute(stmt_movie)
    result = result.scalar()
    if result:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_schema.name}' "
                   f"and release date '{movie_schema.date}' already exists."
        )

    def no_schema_error(schema_name: str) -> HTTPException:
        raise HTTPException(status_code=400, detail=f"{schema_name} in Null")

    country_schema = movie_schema.country
    stmt_country = select(CountryModel).filter(CountryModel.code == country_schema)
    country = await db.execute(stmt_country)
    country = country.scalar()
    if not country:
        country = CountryModel(code=country_schema, name=country_schema.short_name)
        db.add(country)

    genres_coro = [get_coro_func(db_model=GenreModel, schema_attr=genre_name) for genre_name in movie_schema.genres]
    genres = await asyncio.gather(*genres_coro)
    if not genres:
        no_schema_error("genres")

    actors_coro = [get_coro_func(db_model=ActorModel, schema_attr=actor_name) for actor_name in movie_schema.actors]
    actors = await asyncio.gather(*actors_coro)
    actors = [actor for actor in actors if actor]

    languages_coro = [
        get_coro_func(db_model=LanguageModel, schema_attr=language_name)
        for language_name in movie_schema.languages
    ]
    languages = await asyncio.gather(*languages_coro)
    if not languages:
        no_schema_error("languages")

    movie_db = MovieModel(
        name=movie_schema.name,
        date=movie_schema.date,
        score=movie_schema.score,
        overview=movie_schema.overview,
        status=movie_schema.status,
        budget=movie_schema.budget,
        revenue=movie_schema.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages
    )
    db.add(movie_db)
    await db.commit()
    return movie_db


async def delete_movie(movie_id: int, db: AsyncSession):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar()
    if not movie:
        return JSONResponse(status_code=404, content={"detail": "Movie with the given ID was not found."})
    await db.delete(movie)
    await db.commit()


async def update_movie(movie_update_fields: MovieUpdateSchema, movie_id: int, db: AsyncSession):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar()
    if not movie:
        return JSONResponse(status_code=404, content={"detail": "Movie with the given ID was not found."})
    fields = movie_update_fields.model_dump()
    for field, value in fields.items():
        if value:
            setattr(movie, field, value)
    await db.commit()
    return {"detail": "Movie updated successfully."}
