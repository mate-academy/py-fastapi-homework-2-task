from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode
from pydantic import ValidationError

from crud.movies import (
    get_movie_by_id,
    get_movies_page,
    delete_movie as crud_delete_movie,
    create_movie as crud_create_movie,
    update_movie as crud_update_movie,
)
from crud.exceptions import (
    MovieAlreadyExistsException,
    MovieNotFoundException,
)

from database import get_db
from schemas.movies import (
    MovieCreateSchema,
    MovieResponseSchema,
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    CountryResponseSchema,
    NamedEntityResponseSchema,
)
from config.settings import API_V1_PREFIX


router = APIRouter(redirect_slashes=False)


@router.get("/", response_model=MovieListResponseSchema)
async def list_movies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    offset = (page - 1) * per_page
    movies, total = await get_movies_page(db, offset, per_page)
    if total == 0:
        raise HTTPException(status_code=404, detail="No movies found")

    if offset >= total and total > 0:
        raise HTTPException(status_code=404, detail="Movie page not found")

    path = request.url.path.removeprefix(API_V1_PREFIX)

    prev_page = None
    if page > 1:
        prev_page = (
            f"{path}?"
            f"{urlencode({'page': page - 1, 'per_page': per_page})}"
        )

    next_page = None
    if offset + per_page < total:
        next_page = (
            f"{path}?"
            f"{urlencode({'page': page + 1, 'per_page': per_page})}"
        )

    total_pages = (total + per_page - 1) // per_page

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total
    )


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    try:
        movie = await crud_create_movie(movie_data, db)
        return MovieDetailSchema.model_validate(movie)
    except ValidationError:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid input data."}
        )
    except MovieAlreadyExistsException:
        return JSONResponse(
            status_code=409,
            content={
                "detail": f"A movie with the name {movie_data.name} "
                          f"and date {movie_data.date} already exists."
            }
        )


@router.get("/{movie_id}", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> MovieDetailSchema:
    try:
        movie = await get_movie_by_id(movie_id, db)
        return MovieDetailSchema(
            id=movie.id,
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country=CountryResponseSchema(
                id=movie.country.id,
                code=movie.country.code,
                name=movie.country.name
            ) if movie.country else None,
            genres=[NamedEntityResponseSchema(id=genre.id, name=genre.name) for genre in movie.genres],
            actors=[NamedEntityResponseSchema(id=actor.id, name=actor.name) for actor in movie.actors],
            languages=[NamedEntityResponseSchema(id=language.id, name=language.name) for language in movie.languages],
        )
    except MovieNotFoundException:
        return JSONResponse(
            status_code=404,
            content={"detail": "Movie with the given ID was not found."}
        )


@router.patch("/{movie_id}", status_code=200)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    try:
        await crud_update_movie(movie_id, movie_data, db)
        return JSONResponse(
            status_code=200,
            content={"detail": "Movie updated successfully."}
        )
    except ValidationError:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid input data."}
        )
    except MovieNotFoundException:
        return JSONResponse(
            status_code=404,
            content={"detail": "Movie with the given ID was not found."}
        )


@router.delete("/{movie_id}", status_code=204)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    try:
        await crud_delete_movie(movie_id, db)
        return JSONResponse(status_code=204, content=None)
    except MovieNotFoundException:
        return JSONResponse(
            status_code=404,
            content={"detail": "Movie with the given ID was not found."}
        )
