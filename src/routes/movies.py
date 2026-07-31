import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import (
    MovieListResponseSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)
from schemas.movies import get_pagination_urls

from routes import crud

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_all_movies(
    request: Request,
    db: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    total_items = await crud.get_movie_items_count(db=db)
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_pages = math.ceil(total_items / per_page)
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "loc": ["query", "page"],
                "msg": "ensure this value is greater than or equal to 1",
                "type": "value_error.number.not_ge",
            },
        )
    if per_page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "loc": ["query", "per_page"],
                "msg": "ensure this value is greater than or equal to 1",
                "type": "value_error.number.not_ge",
            },
        )
    if per_page > 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "loc": ["query", "per_page"],
                "msg": "ensure this value is less than or equal to 20",
                "type": "value_error.number.not_le",
            },
        )
    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    offset = (page - 1) * per_page
    movies = await crud.get_movie_list(db=db, offset=offset, per_page=per_page)
    if len(movies) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    prev_page, next_page = get_pagination_urls(
        request=request, per_page=per_page, page=page, total=total_items
    )
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED
)
async def create_movie(db: SessionDep, movie: MovieCreateSchema):
    return await crud.create_movie(db=db, movie=movie)


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def read_movie(db: SessionDep, movie_id: int):
    movie = await crud.get_movie_by_id(db=db, movie_id=movie_id)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    return movie


@router.delete("/movies/{movie_id}/")
async def delete_movie(db: SessionDep, movie_id: int):
    deleted = await crud.delete_movie_by_id(db=db, movie_id=movie_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/movies/{movie_id}/")
async def update_movie(db: SessionDep, movie_id: int, movie_payload: MovieUpdateSchema):
    await crud.update_movie(db=db, movie_id=movie_id, movie_payload=movie_payload)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "Movie updated successfully."},
    )
