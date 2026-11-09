from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import MovieModel, get_db
from database.models import ActorModel, CountryModel, GenreModel, LanguageModel
from schemas.movies import (
    MovieCreateSchema,
    MovieDetailSchema,
    MovieListResponseSchema,
    MovieUpdateSchema,
)


class MovieValidationRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def handle_request(request: Request):
            try:
                return await original_handler(request)
            except RequestValidationError as exc:
                if request.method in {"POST", "PATCH"} and all(
                    error["loc"][0] == "body" for error in exc.errors()
                ):
                    raise HTTPException(status_code=400, detail="Invalid input data.") from exc
                raise

        return handle_request


router = APIRouter(route_class=MovieValidationRoute)


async def get_or_create_entity(db, model, field_name, value):
    field = getattr(model, field_name)
    entity = await db.scalar(select(model).where(field == value))
    if entity is not None:
        return entity

    entity = model(**{field_name: value})
    db.add(entity)
    await db.flush()
    return entity


async def get_movie_or_404(db: AsyncSession, movie_id: int) -> MovieModel:
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = (total_items + per_page - 1) // per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel)
        .order_by(MovieModel.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(data: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    duplicate_message = f"A movie with the name '{data.name}' and release date '{data.date}' already exists."
    duplicate_query = select(MovieModel.id).where(MovieModel.name == data.name, MovieModel.date == data.date)
    if await db.scalar(duplicate_query) is not None:
        raise HTTPException(status_code=409, detail=duplicate_message)

    values = data.model_dump(exclude={"country", "genres", "actors", "languages"})
    related_count = 1 + sum(len(set(items)) for items in (data.genres, data.actors, data.languages))
    for attempt in range(related_count + 1):
        creating_related = True
        try:
            country = await get_or_create_entity(db, CountryModel, "code", data.country)
            genres = [await get_or_create_entity(db, GenreModel, "name", name) for name in dict.fromkeys(data.genres)]
            actors = [await get_or_create_entity(db, ActorModel, "name", name) for name in dict.fromkeys(data.actors)]
            languages = [
                await get_or_create_entity(db, LanguageModel, "name", name) for name in dict.fromkeys(data.languages)
            ]
            creating_related = False
            movie = MovieModel(**values, country=country, genres=genres, actors=actors, languages=languages)
            db.add(movie)
            await db.commit()
            return movie
        except IntegrityError as exc:
            await db.rollback()
            if await db.scalar(duplicate_query) is not None:
                raise HTTPException(status_code=409, detail=duplicate_message) from exc
            if not creating_related or attempt == related_count:
                raise


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_or_404(db, movie_id)
    await db.delete(movie)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_or_404(db, movie_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.") from exc
    return {"detail": "Movie updated successfully."}
